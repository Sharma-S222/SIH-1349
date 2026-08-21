"""RF-DETR Medium detector implementing the PersonObjectDetector interface."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import torch

from .config import DetectorConfig

# COCO 90-category mapping (1-indexed, sparse) as used by RF-DETR
COCO_90_NAMES: dict[int, str] = {
    1: "person", 2: "bicycle", 3: "car", 4: "motorcycle", 5: "airplane",
    6: "bus", 7: "train", 8: "truck", 9: "boat", 10: "traffic light",
    11: "fire hydrant", 13: "stop sign", 14: "parking meter", 15: "bench",
    16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep",
    21: "cow", 22: "elephant", 23: "bear", 24: "zebra", 25: "giraffe",
    27: "backpack", 28: "umbrella", 31: "handbag", 32: "tie",
    33: "suitcase", 34: "frisbee", 35: "skis", 36: "snowboard",
    37: "sports ball", 38: "kite", 39: "baseball bat", 40: "baseball glove",
    41: "skateboard", 42: "surfboard", 43: "tennis racket", 44: "bottle",
    46: "wine glass", 47: "cup", 48: "fork", 49: "knife", 50: "spoon",
    51: "bowl", 52: "banana", 53: "apple", 54: "sandwich", 55: "orange",
    56: "broccoli", 57: "carrot", 58: "hot dog", 59: "pizza", 60: "donut",
    61: "cake", 62: "chair", 63: "couch", 64: "potted plant", 65: "bed",
    67: "dining table", 70: "toilet", 72: "tv", 73: "laptop", 74: "mouse",
    75: "remote", 76: "keyboard", 77: "cell phone", 78: "microwave",
    79: "oven", 80: "toaster", 81: "sink", 82: "refrigerator", 84: "book",
    85: "clock", 86: "vase", 87: "scissors", 88: "teddy bear",
    89: "hair drier", 90: "toothbrush",
}

# Map COCO 90-category IDs to 0-indexed positions for detection-v1 compatibility
COCO_90_TO_0INDEXED: dict[int, int] = {}
_COCO_80 = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass",
    "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
    "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
    "teddy bear", "hair drier", "toothbrush",
)
for _idx, _name in enumerate(_COCO_80):
    for _coco_id, _coco_name in COCO_90_NAMES.items():
        if _coco_name == _name:
            COCO_90_TO_0INDEXED[_coco_id] = _idx
            break

# Inverse: 0-indexed ID → COCO 90 ID
INDEXED_TO_COCO_90: dict[int, int] = {v: k for k, v in COCO_90_TO_0INDEXED.items()}


class PersonObjectDetector:
    """RF-DETR Medium detector returning detection-v1 dictionaries from OpenCV frames."""

    def __init__(self, config: Optional[DetectorConfig] = None) -> None:
        self.config = config or DetectorConfig()
        self.device = torch.device(
            self.config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self._load_model()
        self._warmup_done = False

    def _load_model(self) -> None:
        from rfdetr import RFDETRMedium

        weights = str(self.config.rf_detr_weights_path)
        if not Path(weights).exists():
            raise FileNotFoundError(f"RF-DETR weights not found: {weights}")

        self._model = RFDETRMedium(pretrain_weights=weights)
        if self.device.type == "cuda":
            self._model.inference(dtype=torch.float16)

    def _warmup(self, frame: np.ndarray) -> None:
        if not self._warmup_done:
            self._model.predict(frame, threshold=0.5, include_source_image=False)
            self._warmup_done = True

    def detect_frame(
        self,
        frame: np.ndarray,
        camera_id: str = "CAM_01",
        frame_index: int = 0,
        timestamp_ms: Optional[int] = None,
    ) -> dict[str, Any]:
        """Analyse one BGR OpenCV frame and return the detection-v1 contract."""
        if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("frame must be a BGR NumPy array shaped (height, width, 3)")

        height, width = frame.shape[:2]
        self._warmup(frame)

        started = time.perf_counter()
        detections = self._model.predict(
            frame,
            threshold=self.config.confidence_threshold,
            include_source_image=False,
        )
        inference_ms = (time.perf_counter() - started) * 1000

        result_detections: list[dict[str, Any]] = []
        for i in range(len(detections)):
            coco_cat_id = int(detections.class_id[i])
            confidence = float(detections.confidence[i])

            # Map COCO 90-category ID to 0-indexed for detection-v1 compatibility
            class_id = COCO_90_TO_0INDEXED.get(coco_cat_id, coco_cat_id)
            class_name = COCO_90_NAMES.get(coco_cat_id, _COCO_80[class_id] if class_id < len(_COCO_80) else str(class_id))

            if class_name not in self.config.allowed_classes:
                continue

            x1, y1, x2, y2 = (int(round(v)) for v in detections.xyxy[i].tolist())
            x1, x2 = max(0, min(x1, width)), max(0, min(x2, width))
            y1, y2 = max(0, min(y1, height)), max(0, min(y2, height))

            result_detections.append(
                {
                    "detection_id": f"det_{len(result_detections) + 1}",
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "bbox_xyxy": [x1, y1, x2, y2],
                }
            )

        return {
            "schema_version": "detection-v1",
            "camera_id": camera_id,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms if timestamp_ms is not None else 0,
            "frame_width": width,
            "frame_height": height,
            "people_count": sum(d["class_name"] == "person" for d in result_detections),
            "detections": result_detections,
            "inference_ms": round(inference_ms, 2),
            "model": {"name": self.config.model_name, "version": self.config.model_version},
        }
