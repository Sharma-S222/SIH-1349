from dataclasses import dataclass
from typing import Any


EXPECTED_SCHEMA_VERSION = "detection-v1"


@dataclass
class Detection:
    """
    Internal representation of one Member 1 detection.

    detection_id:
        Frame-local ID created by Member 1.

    track_id:
        NOT stored here.
        Track identity is created later by Member 2's tracker.
    """

    detection_id: str
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
            (x1 + x2) / 2.0,
            (y1 + y2) / 2.0,
        )

    @property
    def foot_point(self) -> tuple[float, float]:
        x1, _, x2, y2 = self.bbox_xyxy

        return (
            (x1 + x2) / 2.0,
            y2,
        )

    def to_xywh(self) -> list[float]:
        """
        Convert internal xyxy representation to xywh.

        Member 1's shared contract remains xyxy.
        This conversion is only for components that need xywh.
        """
        x1, y1, x2, y2 = self.bbox_xyxy

        return [
            x1,
            y1,
            x2 - x1,
            y2 - y1,
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox_xyxy": self.bbox_xyxy,
            "width": self.width,
            "height": self.height,
            "center": list(self.center),
            "foot_point": list(self.foot_point),
        }


def _parse_bbox(
    raw_bbox: Any,
    detection_id: str,
) -> list[float]:
    """
    Validate and normalize Member 1's bbox_xyxy.
    """

    if not isinstance(raw_bbox, (list, tuple)):
        raise ValueError(
            f"Detection {detection_id}: "
            "bbox_xyxy must be a list or tuple"
        )

    if len(raw_bbox) != 4:
        raise ValueError(
            f"Detection {detection_id}: "
            "bbox_xyxy must contain exactly 4 values"
        )

    try:
        x1, y1, x2, y2 = map(float, raw_bbox)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Detection {detection_id}: "
            "bbox_xyxy contains non-numeric values"
        ) from exc

    if x2 <= x1:
        raise ValueError(
            f"Detection {detection_id}: "
            "bbox x2 must be greater than x1"
        )

    if y2 <= y1:
        raise ValueError(
            f"Detection {detection_id}: "
            "bbox y2 must be greater than y1"
        )

    return [
        x1,
        y1,
        x2,
        y2,
    ]


def _parse_confidence(
    raw_confidence: Any,
    detection_id: str,
) -> float:
    """
    Validate Member 1 confidence.
    """

    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Detection {detection_id}: "
            "confidence must be numeric"
        ) from exc

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"Detection {detection_id}: "
            f"confidence must be between 0 and 1, "
            f"got {confidence}"
        )

    return confidence


def _parse_detection(
    raw: Any,
    index: int,
) -> Detection:
    """
    Convert one raw Member 1 detection into a Detection object.
    """

    if not isinstance(raw, dict):
        raise ValueError(
            f"Detection at index {index} must be an object"
        )

    # ---------------------------------------------------------
    # detection_id
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # Member 1 owns this ID.
    #
    # Example:
    #     "det_0_0"
    #
    # It MUST remain a string.
    # Do not convert it to int.
    # Do not generate a replacement ID.
    # ---------------------------------------------------------

    if "detection_id" not in raw:
        raise ValueError(
            f"Detection at index {index}: "
            "missing required detection_id"
        )

    detection_id = raw["detection_id"]

    if not isinstance(detection_id, str):
        raise ValueError(
            f"Detection at index {index}: "
            "detection_id must be a string"
        )

    if not detection_id.strip():
        raise ValueError(
            f"Detection at index {index}: "
            "detection_id cannot be empty"
        )

    # ---------------------------------------------------------
    # class_id
    # ---------------------------------------------------------

    if "class_id" not in raw:
        raise ValueError(
            f"Detection {detection_id}: "
            "missing required class_id"
        )

    try:
        class_id = int(raw["class_id"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Detection {detection_id}: "
            "class_id must be an integer"
        ) from exc

    # ---------------------------------------------------------
    # class_name
    # ---------------------------------------------------------

    class_name = raw.get("class_name")

    if not isinstance(class_name, str) or not class_name.strip():
        raise ValueError(
            f"Detection {detection_id}: "
            "class_name must be a non-empty string"
        )

    # ---------------------------------------------------------
    # confidence
    # ---------------------------------------------------------

    if "confidence" not in raw:
        raise ValueError(
            f"Detection {detection_id}: "
            "missing required confidence"
        )

    confidence = _parse_confidence(
        raw["confidence"],
        detection_id,
    )

    # ---------------------------------------------------------
    # bounding box
    # ---------------------------------------------------------

    if "bbox_xyxy" not in raw:
        raise ValueError(
            f"Detection {detection_id}: "
            "missing required bbox_xyxy"
        )

    bbox_xyxy = _parse_bbox(
        raw["bbox_xyxy"],
        detection_id,
    )

    return Detection(
        detection_id=detection_id,
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
        bbox_xyxy=bbox_xyxy,
    )


def adapt_detections(
    frame: dict[str, Any],
) -> list[Detection]:
    """
    Convert Member 1's detection-v1 frame into
    clean internal Detection objects.

    Expected input:

        {
            "schema_version": "detection-v1",
            "camera_id": null,
            "frame_index": 0,
            "timestamp_ms": 0,
            "frame_width": 810,
            "frame_height": 1080,
            "people_count": 4,
            "detections": [...]
        }

    The adapter intentionally does NOT require:

        track_id
        inference_ms
        model

    Those do not belong to Member 1's detection contract.
    """

    if not isinstance(frame, dict):
        raise ValueError(
            "Member 1 frame must be a JSON object"
        )

    # ---------------------------------------------------------
    # Schema validation
    # ---------------------------------------------------------

    schema_version = frame.get("schema_version")

    if schema_version != EXPECTED_SCHEMA_VERSION:
        raise ValueError(
            "Invalid Member 1 schema version: "
            f"expected '{EXPECTED_SCHEMA_VERSION}', "
            f"got {schema_version!r}"
        )

    # ---------------------------------------------------------
    # Required frame fields
    # ---------------------------------------------------------

    if "frame_index" not in frame:
        raise ValueError(
            "Member 1 frame is missing frame_index"
        )

    if not isinstance(frame["frame_index"], int):
        raise ValueError(
            "frame_index must be an integer"
        )

    if "timestamp_ms" not in frame:
        raise ValueError(
            "Member 1 frame is missing timestamp_ms"
        )

    if not isinstance(frame["timestamp_ms"], int):
        raise ValueError(
            "timestamp_ms must be an integer"
        )

    # camera_id is allowed to be null because your
    # current system uses one camera and the contract allows it.
    camera_id = frame.get("camera_id")

    if camera_id is not None and not isinstance(camera_id, str):
        raise ValueError(
            "camera_id must be a string or null"
        )

    # ---------------------------------------------------------
    # Detections
    # ---------------------------------------------------------

    raw_detections = frame.get("detections")

    if raw_detections is None:
        raise ValueError(
            "Member 1 frame is missing detections"
        )

    if not isinstance(raw_detections, list):
        raise ValueError(
            "detections must be a list"
        )

    detections: list[Detection] = []

    for index, raw_detection in enumerate(raw_detections):

        detection = _parse_detection(
            raw_detection,
            index,
        )

        detections.append(detection)

    return detections