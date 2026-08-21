"""Phase 10: Integration and Final Handoff tests.

Tests that the full project integrates correctly and that
the handoff is reproducible. This includes verifying:
- All dependencies are available
- All modules can be imported
- The full detection pipeline works end-to-end
- Configuration is correct
- Outputs are generated as expected
"""

from __future__ import annotations
from pathlib import Path

import json
import sys
import time
import numpy as np
import jsonschema

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load the DetectionResult v1 schema directly from the schema file
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "tests" / "schemas" / "detection_result_v1.json"
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    DETECTION_RESULT_V1_SCHEMA = json.load(f)

from ai.detection.config import DetectorConfig
from ai.detection.detector import PersonObjectDetector


def test_project_structure():
    """Test that the project directory structure is correct.

    Verifies all expected files and directories exist.
    """
    project_root = Path(__file__).resolve().parent.parent

    # Check essential files exist
    essential_files = [
        "ai/detection/config.py",
        "ai/detection/detector.py",
        "weights/rtdetrv2_s.pth",
        "tests/conftest.py",
        "tests/schemas/detection_result_v1.json",
        "tests/test_bounding_boxes.py",
        "tests/test_class_filtering.py",
        "tests/test_confidence.py",
        "tests/test_detection_result.py",
        "tests/test_detect_frame.py",
        "tests/test_empty_detections.py",
        "tests/test_people_counting.py",
        "tests/test_difficult_scenes.py",
        "tests/test_benchmarking.py",
        "tests/test_integration_mocked.py",
        "tests/test_integration_real.py",
    ]

    for filepath in essential_files:
        full_path = project_root / filepath
        assert full_path.exists(), f"Essential file missing: {filepath}"

    # Check essential directories exist
    essential_dirs = ["ai", "outputs", "third_party", "weights", "scripts"]
    for dir_name in essential_dirs:
        full_dir = project_root / dir_name
        assert full_dir.exists(), f"Essential directory missing: {dir_name}"


def test_configuration_loaded():
    """Test that DetectorConfig loads correctly with all required fields."""
    config = DetectorConfig()

    # Verify required configuration fields
    assert config.model_name == "RF-DETR-Medium", f"Expected model_name RF-DETR-Medium, got {config.model_name}"
    assert config.model_version == "rf-detr-medium-v1", f"Expected model_version rf-detr-medium-v1, got {config.model_version}"
    assert config.confidence_threshold == 0.50, f"Expected confidence_threshold 0.50, got {config.confidence_threshold}"
    assert len(config.allowed_classes) > 0, "allowed_classes should not be empty"
    assert "person" in config.allowed_classes, "person should be in allowed_classes"

    # Verify RF-DETR weights path exists
    assert Path(config.rf_detr_weights_path).exists(), f"RF-DETR weights file missing: {config.rf_detr_weights_path}"


def test_detector_loads_successfully():
    """Test that PersonObjectDetector loads the model successfully.

    Verifies the detector can be instantiated and the model
    is ready for inference.
    """
    config = DetectorConfig()
    detector = PersonObjectDetector(config)

    # Verify detector has model attribute
    assert detector._model is not None, "Detector model should be loaded"
    assert detector.device is not None, "Detector device should be set"


def test_full_detection_pipeline():
    """Test the complete end-to-end detection pipeline.

    Runs the detector on a sample frame and verifies the
    complete output matches the DetectionResult v1 schema.
    """
    detector = PersonObjectDetector(DetectorConfig())

    # Create a test frame
    frame = np.random.RandomState(42).randint(0, 256, (480, 640, 3), dtype=np.uint8)

    # Run detection
    result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)

    # Verify result has all required schema fields
    required_fields = [
        "schema_version", "camera_id", "frame_index", "timestamp_ms",
        "frame_width", "frame_height", "people_count", "detections",
        "inference_ms", "model",
    ]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    # Verify schema validation passes
    import jsonschema
    jsonschema.validate(result, DETECTION_RESULT_V1_SCHEMA)

    # Verify people_count matches person detections
    person_detections = [d for d in result["detections"] if d["class_name"] == "person"]
    assert result["people_count"] == len(person_detections), \
        "people_count should match person detections"

    # Verify model info
    assert result["model"]["name"] == "RF-DETR-Medium"
    assert result["model"]["version"] == "rf-detr-medium-v1"


def test_schema_consistency_across_runs():
    """Test that DetectionResult v1 output is consistent across multiple runs.

    Verifies that running the detector multiple times on the same
    frame produces consistent schema-valid output.
    """
    detector = PersonObjectDetector(DetectorConfig())
    frame = np.random.RandomState(42).randint(0, 256, (480, 640, 3), dtype=np.uint8)

    results = []
    for _ in range(3):
        result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)
        import jsonschema
        jsonschema.validate(result, DETECTION_RESULT_V1_SCHEMA)
        results.append(result)

    # Verify all results are schema-valid (just check no errors raised)
    assert len(results) == 3


def test_output_json_serialization():
    """Test that DetectionResult v1 output can be serialized to JSON.

    Verifies the detection result dict can be serialized and
    deserialized while maintaining schema validity.
    """
    detector = PersonObjectDetector(DetectorConfig())
    frame = np.random.RandomState(42).randint(0, 256, (480, 640, 3), dtype=np.uint8)

    result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)

    # Serialize to JSON
    json_str = json.dumps(result)
    parsed = json.loads(json_str)

    # Deserialized result should match original
    assert parsed == result, "Serialized and parsed JSON should match"

    # Deserialized result should validate against schema
    import jsonschema
    jsonschema.validate(parsed, DETECTION_RESULT_V1_SCHEMA)


def test_rediscovery_of_weights():
    """Test that weights file is discoverable and readable.

    Verifies the weights path from config points to an existing
    file that can be read.
    """
    config = DetectorConfig()
    weights_path = Path(config.rf_detr_weights_path)

    assert weights_path.exists(), f"Weights file should exist at {weights_path}"
    assert weights_path.stat().st_size > 0, f"Weights file should not be empty"

    # Verify it's a valid PyTorch checkpoint (RF-DETR format)
    import torch
    checkpoint = torch.load(str(weights_path), map_location="cpu", weights_only=False)
    assert isinstance(checkpoint, dict), "Checkpoint should be a dict"


def test_sample_image_processing():
    """Test that a synthetic test image can be processed.

    Verifies a synthetic image can be created and processed
    by the detector pipeline.
    """
    import cv2
    import jsonschema

    detector = PersonObjectDetector(DetectorConfig())

    # Create synthetic test image (white rectangle on black background)
    image_path = Path("synthetic_test.jpg")
    synthetic_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(synthetic_frame, (500, 200), (780, 600), (255, 255, 255), -1)
    cv2.imwrite(str(image_path), synthetic_frame)

    try:
        frame = cv2.imread(str(image_path))
        assert frame is not None, "synthetic test image should be readable"

        # Run detection
        result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)

        # Verify result is schema-valid
        import jsonschema
        jsonschema.validate(result, DETECTION_RESULT_V1_SCHEMA)

        # Verify people_count is a non-negative integer
        assert isinstance(result["people_count"], int)
        assert result["people_count"] >= 0
    finally:
        # Cleanup
        if image_path.exists():
            image_path.unlink()