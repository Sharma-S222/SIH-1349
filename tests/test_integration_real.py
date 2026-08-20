"""Real-model integration test for PersonObjectDetector.

Tests the complete inference pipeline with the actual RT-DETRv2-S detector.
This test loads the real model and processes a synthetic frame, verifying
the complete output-assembly path with the actual model execution.

Requires:
- Model weights at weights/rtdetrv2_s.pth (exists in project)
- RT-DETRv2-PyTorch source at third_party/RT-DETR/rtdetrv2_pytorch
- Config at ai/detection/config.py

Verifies the complete pipeline:
- Model loading and inference
- Detection result creation
- DetectionResult v1 schema validation
- Bounding box validity
- Confidence score validity
- Allowed classes
- People counting
- Camera ID propagation
- Output serialization
- Schema validation of serialized output
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.detection.detector import PersonObjectDetector
from ai.detection.config import DetectorConfig
import json
from pathlib import Path

# Load the DetectionResult v1 schema directly from the schema file
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "tests" / "schemas" / "detection_result_v1.json"
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    DETECTION_RESULT_V1_SCHEMA = json.load(f)


def _validate_schema(data):
    """Validate data against the DetectionResult v1 schema."""
    import jsonschema

    jsonschema.validate(data, DETECTION_RESULT_V1_SCHEMA)


def test_real_model_integration():
    """Integration test for RT-DETRv2-S real model inference.

    Requires:
    - Model weights at weights/rtdetrv2_s.pth
    - Config at ai/detection/config.py

    Verifies the complete pipeline with the actual RT-DETRv2-S model:
    - Model loading and inference
    - Detection result creation
    - DetectionResult v1 schema validation
    - Bounding box validity
    - Confidence score validity
    - Allowed classes
    - People counting
    - Camera ID propagation
    - Output serialization
    - Schema validation of serialized output
    """
    # initialise detector with default config
    config = DetectorConfig()
    detector = PersonObjectDetector(config)

    # create a synthetic deterministic frame
    frame = np.random.RandomState(42).randint(0, 256, (480, 640, 3), dtype=np.uint8)

    # run real model inference
    result = detector.detect_frame(
        frame,
        camera_id="CAM_01",
        frame_index=0,
    )

    # verify the result is a valid dict with expected keys
    assert isinstance(result, dict), "detect_frame() should return a dict"
    required_keys = [
        "schema_version", "camera_id", "frame_index", "timestamp_ms",
        "frame_width", "frame_height", "people_count", "detections",
        "inference_ms", "model",
    ]
    for key in required_keys:
        assert key in result, f"Missing key '{key}' in DetectionResult"

    # verify schema_version
    assert result["schema_version"] == "1.0", "schema_version should be '1.0'"

    # verify camera_id propagation
    assert result["camera_id"] == "CAM_01", "camera_id should be CAM_01"

    # verify frame dimensions
    assert result["frame_width"] == 640, "frame_width should be 640"
    assert result["frame_height"] == 480, "frame_height should be 480"

    # verify people_count matches person detections
    person_detections = [d for d in result["detections"] if d["class_name"] == "person"]
    assert result["people_count"] == len(person_detections), \
        f"people_count ({result['people_count']}) should match person detections ({len(person_detections)})"

    # verify inference_ms is positive (model actually ran)
    assert result["inference_ms"] > 0, "inference_ms should be positive (model executed)"
    assert isinstance(result["inference_ms"], float), "inference_ms should be a float"

    # verify model info
    assert result["model"]["name"] == "RT-DETRv2-S", "model name should be RT-DETRv2-S"
    assert result["model"]["version"] == "baseline-v1", "model version should be baseline-v1"

    # verify each detection has required fields and valid values
    for detection in result["detections"]:
        required_detection_keys = [
            "detection_id", "class_id", "class_name", "confidence", "bbox_xyxy"
        ]
        for key in required_detection_keys:
            assert key in detection, f"Missing key '{key}' in detection"

        # verify bbox_xyxy has 4 elements
        bbox = detection["bbox_xyxy"]
        assert len(bbox) == 4, f"bbox_xyxy should have 4 elements, got {len(bbox)}"
        x1, y1, x2, y2 = bbox
        assert x2 > x1, f"x2 ({x2}) should be greater than x1 ({x1})"
        assert y2 > y1, f"y2 ({y2}) should be greater than y1 ({y1})"
        assert x1 >= 0, f"x1 ({x1}) should be non-negative"
        assert y1 >= 0, f"y1 ({y1}) should be non-negative"
        assert 0.0 <= detection["confidence"] <= 1.0, \
            f"confidence {detection['confidence']} should be in [0, 1]"

        # verify class_name is in allowed classes
        assert detection["class_name"] in config.allowed_classes, \
            f"Detected class {detection['class_name']} not in allowed classes {config.allowed_classes}"

    # schema validation against DetectionResult v1 JSON Schema
    _validate_schema(result)

    # verify output can be re-serialized and still validate
    json_line = json.dumps(result)
    parsed = json.loads(json_line)
    assert parsed == result, "Serialized and parsed JSON should match original"
    _validate_schema(parsed)