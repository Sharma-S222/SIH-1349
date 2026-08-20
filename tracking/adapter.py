from dataclasses import dataclass
from typing import Any


@dataclass
class Detection:
    detection_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: list[float]

    @property
    def width(self) -> float:
        return self.bbox_xyxy[2] - self.bbox_xyxy[0]

    @property
    def height(self) -> float:
        return self.bbox_xyxy[3] - self.bbox_xyxy[1]

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy

        return (
            (x1 + x2) / 2,
            (y1 + y2) / 2,
        )

    @property
    def foot_point(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy

        return (
            (x1 + x2) / 2,
            y2,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox_xyxy": self.bbox_xyxy,
            "width": self.width,
            "height": self.height,
            "center": self.center,
            "foot_point": self.foot_point,
        }


def adapt_detections(frame: dict[str, Any]) -> list[Detection]:
    """
    Convert Member 1's detection-v1 frame into
    clean internal Detection objects.
    """

    detections = []

    for raw in frame.get("detections", []):

        bbox = raw.get("bbox_xyxy")

        if not bbox or len(bbox) != 4:
            continue

        confidence = float(
            raw.get("confidence", 0.0)
        )

        # Ignore invalid detections
        if confidence < 0.0 or confidence > 1.0:
            continue

        x1, y1, x2, y2 = map(float, bbox)

        # Ignore invalid bounding boxes
        if x2 <= x1 or y2 <= y1:
            continue

        detection = Detection(
            detection_id=int(
                raw.get("detection_id", len(detections))
            ),
            class_id=int(
                raw.get("class_id", 0)
            ),
            class_name=str(
                raw.get("class_name", "unknown")
            ),
            confidence=confidence,
            bbox_xyxy=[
                x1,
                y1,
                x2,
                y2,
            ],
        )

        detections.append(detection)

    return detections