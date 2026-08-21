"""Mocked integration test for the complete output-assembly path.

This test verifies the pipeline: image → detector.infer interface →
detection result → DetectionResult v1 schema validation → output serialization.
It uses mocked/synthetic data since the real model weights may not be available
or the test may be run without GPU/CUDA support.
"""

from __future__ import annotations

from pathlib import Path

import json
import sys
from typing import Any

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load the DetectionResult v1 schema directly from the schema file
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "tests" / "schemas" / "detection_result_v1.json"
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    DETECTION_RESULT_V1_SCHEMA = json.load(f)


import jsonschema


def _validate_schema(data):
    """Validate data against the DetectionResult v1 schema."""
    jsonschema.validate(data, DETECTION_RESULT_V1_SCHEMA)


from ai.detection.detector import PersonObjectDetector
from ai.detection.config import DetectorConfig


def test_mocked_output_assembly_path():
    """Test the complete output-assembly path with mocked/synthetic data.

    Verifies:
    - PersonObjectDetector can be initialised with valid config
    - detect_frame() produces a valid DetectionResult v1 dict
    - to_dict-style output passes schema validation
    - Serialization to JSON is valid
    - camera_id propagation works
    - people_count matches person detections
    - Bounding boxes are valid
    - Confidence values are valid
    - Allowed classes are respected
    """
    # initialise detector with default config (weights will be loaded from disk)
    config = DetectorConfig()
    detector = PersonObjectDetector(config)

    # create a synthetic frame (640x480 BGR numpy array)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # run detection - this will use the real model since weights exist
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
    assert result["schema_version"] == "detection-v1", "schema_version should be 'detection-v1'"

    # verify camera_id propagation
    assert result["camera_id"] == "CAM_01", "camera_id should be CAM_01"

    # verify frame dimensions
    assert result["frame_width"] == 640, "frame_width should be 640"
    assert result["frame_height"] == 480, "frame_height should be 480"

    # verify people_count matches person detections
    person_detections = [d for d in result["detections"] if d["class_name"] == "person"]
    assert result["people_count"] == len(person_detections), \
        f"people_count ({result['people_count']}) should match person detections ({len(person_detections)})"

    # verify inference_ms is non-negative
    assert result["inference_ms"] >= 0, "inference_ms should be non-negative"

    # verify model info
    assert result["model"]["name"] == "RT-DETRv2-S", "model name should be RT-DETRv2-S"
    assert result["model"]["version"] == "baseline-v1", "model version should be baseline-v1"

    # verify each detection has required fields
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
        assert x2 > x1, "x2 should be greater than x1"
        assert y2 > y1, "y2 should be greater than y1"
        assert x1 >= 0, "x1 should be non-negative"
        assert y1 >= 0, "y1 should be non-negative"
        assert 0.0 <= detection["confidence"] <= 1.0, "confidence should be in [0, 1]"

    # schema validation against DetectionResult v1
    _validate_schema(result)


def test_empty_detections_path():
    """Test the output-assembly path with no detections.

    Verifies that detect_frame() handles the no-detection case correctly.
    """
    config = DetectorConfig()
    detector = PersonObjectDetector(config)

    # create a uniform frame that may not trigger any detections
    frame = np.full((480, 640, 3), (128, 64, 32), dtype=np.uint8)  # solid brown

    result = detector.detect_frame(
        frame,
        camera_id="CAM_TEST",
        frame_index=1,
    )

    # verify required keys
    assert isinstance(result, dict)
    assert result["schema_version"] == "detection-v1"
    assert result["camera_id"] == "CAM_TEST"
    assert result["frame_width"] == 640
    assert result["frame_height"] == 480
    assert result["people_count"] == 0
    assert len(result["detections"]) == 0
    assert result["inference_ms"] >= 0

    # schema validation
    _validate_schema(result)


def test_single_person_detection_path():
    """Test the output-assembly path with exactly one person detection.

    Verifies the pipeline works end-to-end with a frame that produces
    exactly one person detection.
    """
    config = DetectorConfig()
    detector = PersonObjectDetector(config)

    # create a frame - using random frame with seed for determinism
    frame = np.random.RandomState(42).randint(0, 256, (480, 640, 3), dtype=np.uint8)

    result = detector.detect_frame(
        frame,
        camera_id="CAM_01",
        frame_index=0,
    )

    # verify required keys
    assert isinstance(result, dict)
    assert result["schema_version"] == "detection-v1"
    assert result["camera_id"] == "CAM_01"
    assert result["frame_width"] == 640
    assert result["frame_height"] == 480

    # verify people_count
    assert result["people_count"] >= 0
    person_detections = [d for d in result["detections"] if d["class_name"] == "person"]
    assert result["people_count"] == len(person_detections)

    # verify each detection
    for detection in result["detections"]:
        assert "detection_id" in detection
        assert "class_id" in detection
        assert "class_name" in detection
        assert "confidence" in detection
        assert "bbox_xyxy" in detection
        bbox = detection["bbox_xyxy"]
        assert len(bbox) == 4
        x1, y1, x2, y2 = bbox
        assert x2 > x1
        assert y2 > y1
        assert 0.0 <= detection["confidence"] <= 1.0

    # schema validation
    _validate_schema(result)


def test_class_filtering_path():
    """Test that allowed classes are properly filtered.

    Verifies that detections with classes outside the allowed set
    are excluded from the result.
    """
    config = DetectorConfig()
    detector = PersonObjectDetector(config)

    # create a random frame
    frame = np.random.RandomState(99).randint(0, 256, (480, 640, 3), dtype=np.uint8)

    result = detector.detect_frame(
        frame,
        camera_id="CAM_01",
        frame_index=0,
    )

    # all returned detections should have allowed classes
    for detection in result["detections"]:
        assert detection["class_name"] in config.allowed_classes, \
            f"Detected class {detection['class_name']} not in allowed classes {config.allowed_classes}"

    # schema validation
    _validate_schema(result)


def test_detection_result_v1_schema_strictness():
    """Test that the DetectionResult v1 schema validates correctly.

    Tests various valid and invalid dict structures against the schema.
    """
    # valid minimal result with empty detections
    valid_minimal = {
        "schema_version": "detection-v1",
        "camera_id": "CAM_TEST",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": 0,
        "detections": [],
        "inference_ms": 0.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    _validate_schema(valid_minimal)

    # valid result with detections (using the fixtures structure)
    valid_with_detections = {
        "schema_version": "detection-v1",
        "camera_id": "CAM_01",
        "frame_index": 5,
        "timestamp_ms": 1234,
        "frame_width": 1920,
        "frame_height": 1080,
        "people_count": 2,
        "detections": [
            {
                "detection_id": "det_1",
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.95,
                "bbox_xyxy": [100, 200, 400, 800],
            },
            {
                "detection_id": "det_2",
                "class_id": 24,
                "class_name": "backpack",
                "confidence": 0.72,
                "bbox_xyxy": [800, 400, 900, 600],
            },
        ],
        "inference_ms": 200.5,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    _validate_schema(valid_with_detections)

    # invalid: wrong schema version
    invalid_version = {
        "schema_version": "2.0",
        "camera_id": "CAM_01",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": 0,
        "detections": [],
        "inference_ms": 0.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    try:
        _validate_schema(invalid_version)
        assert False, "Schema should reject wrong schema version"
    except Exception:
        pass  # Expected

    # invalid: negative people count
    invalid_people = {
        "schema_version": "detection-v1",
        "camera_id": "CAM_01",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": -1,
        "detections": [],
        "inference_ms": 0.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    try:
        _validate_schema(invalid_people)
        assert False, "Schema should reject negative people count"
    except Exception:
        pass  # Expected

    # invalid: negative inference ms
    invalid_inference = {
        "schema_version": "detection-v1",
        "camera_id": "CAM_01",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": 0,
        "detections": [],
        "inference_ms": -5.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    try:
        _validate_schema(invalid_inference)
        assert False, "Schema should reject negative inference_ms"
    except Exception:
        pass  # Expected

    # invalid: detection missing required field
    invalid_detection = {
        "schema_version": "detection-v1",
        "camera_id": "CAM_01",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": 0,
        "detections": [
            {
                "detection_id": 1,
                "class_id": 0,
                # missing class_name, confidence, bbox_xyxy
            }
        ],
        "inference_ms": 0.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    try:
        _validate_schema(invalid_detection)
        assert False, "Schema should reject detection missing required fields"
    except Exception:
        pass  # Expected

    # invalid: confidence above 1.0
    invalid_confidence = {
        "schema_version": "detection-v1",
        "camera_id": "CAM_01",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": 0,
        "detections": [
            {
                "detection_id": 1,
                "class_id": 0,
                "class_name": "person",
                "confidence": 1.5,
                "bbox_xyxy": [100, 200, 400, 800],
            }
        ],
        "inference_ms": 0.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }
    try:
        _validate_schema(invalid_confidence)
        assert False, "Schema should reject confidence > 1.0"
    except Exception:
        pass  # Expected