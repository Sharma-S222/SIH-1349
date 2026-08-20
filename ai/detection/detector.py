"""Framework-isolated RT-DETRv2-S detector for OpenCV/NumPy frames."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

from .config import DetectorConfig


COCO_CLASSES = (
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


class PersonObjectDetector:
    """Return DetectionResult v1 dictionaries from OpenCV/NumPy image frames."""

    def __init__(self, config: Optional[DetectorConfig] = None) -> None:
        self.config = config or DetectorConfig()
        self.device = torch.device(self.config.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._validate_paths()
        self._load_model()
        self._transform = transforms.Compose([transforms.Resize((640, 640)), transforms.ToTensor()])

    def _validate_paths(self) -> None:
        for path, description in (
            (self.config.model_root, "RT-DETR source directory"),
            (self.config.model_config_path, "RT-DETR model configuration"),
            (self.config.weights_path, "RT-DETRv2-S weights"),
        ):
            if not path.exists():
                raise FileNotFoundError(f"{description} was not found: {path}")

    def _load_model(self) -> None:
        model_root = str(self.config.model_root)
        if model_root not in sys.path:
            sys.path.insert(0, model_root)
        from src.core import YAMLConfig  # Imported only after the vendor source is available.

        cfg = YAMLConfig(str(self.config.model_config_path), resume=str(self.config.weights_path))
        checkpoint = torch.load(self.config.weights_path, map_location=self.device)
        state = checkpoint["ema"]["module"] if "ema" in checkpoint else checkpoint["model"]
        cfg.model.load_state_dict(state)

        class DeployModel(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.model = cfg.model.deploy()
                self.postprocessor = cfg.postprocessor.deploy()

            def forward(self, images: torch.Tensor, original_sizes: torch.Tensor) -> Any:
                return self.postprocessor(self.model(images), original_sizes)

        self._model = DeployModel().to(self.device).eval()

    def detect_frame(
        self,
        frame: np.ndarray,
        camera_id: str = "CAM_01",
        frame_index: int = 0,
        timestamp_ms: Optional[int] = None,
    ) -> dict[str, Any]:
        """Analyse one BGR OpenCV frame and return the DetectionResult v1 contract."""
        if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("frame must be a BGR NumPy array shaped (height, width, 3)")

        height, width = frame.shape[:2]
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        tensor = self._transform(image).unsqueeze(0).to(self.device)
        original_sizes = torch.tensor([[width, height]], device=self.device)

        started = time.perf_counter()
        with torch.inference_mode():
            labels, boxes, scores = self._model(tensor, original_sizes)
        inference_ms = (time.perf_counter() - started) * 1000

        detections: list[dict[str, Any]] = []
        for label, box, score in zip(labels[0], boxes[0], scores[0]):
            confidence = float(score)
            class_id = int(label)
            class_name = COCO_CLASSES[class_id] if 0 <= class_id < len(COCO_CLASSES) else str(class_id)
            if confidence < self.config.confidence_threshold or class_name not in self.config.allowed_classes:
                continue

            x1, y1, x2, y2 = (int(round(value)) for value in box.tolist())
            x1, x2 = max(0, min(x1, width)), max(0, min(x2, width))
            y1, y2 = max(0, min(y1, height)), max(0, min(y2, height))
            detections.append(
                {
                    "detection_id": len(detections) + 1,
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "bbox_xyxy": [x1, y1, x2, y2],
                }
            )

        return {
            "schema_version": "1.0",
            "camera_id": camera_id,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms if timestamp_ms is not None else 0,
            "frame_width": width,
            "frame_height": height,
            "people_count": sum(item["class_name"] == "person" for item in detections),
            "detections": detections,
            "inference_ms": round(inference_ms, 2),
            "model": {"name": self.config.model_name, "version": self.config.model_version},
        }
