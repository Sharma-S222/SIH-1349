"""Tests for DetectionResult v1 schema compliance."""

from __future__ import annotations

from typing import Any

import pytest

try:
    from jsonschema import validate
except ImportError:
    validate = None

pytestmark = pytest.mark.skipif(validate is None, reason="jsonschema not installed")


class TestDetectionResultSchema:
    """Validate DetectionResult dicts against the v1 JSON Schema."""

    def test_empty_detections_valid(
        self, empty_detections_result: dict[str, Any], detection_result_v1_schema: dict
    ) -> None:
        validate(instance=empty_detections_result, schema=detection_result_v1_schema)

    def test_single_person_valid(
        self, single_person_result: dict[str, Any], detection_result_v1_schema: dict
    ) -> None:
        validate(instance=single_person_result, schema=detection_result_v1_schema)

    def test_multi_detection_valid(
        self, multi_detection_result: dict[str, Any], detection_result_v1_schema: dict
    ) -> None:
        validate(instance=multi_detection_result, schema=detection_result_v1_schema)

    def test_missing_required_field(self, detection_result_v1_schema: dict) -> None:
        bad = {"schema_version": "detection-v1"}
        with pytest.raises(Exception):
            validate(instance=bad, schema=detection_result_v1_schema)

    def test_wrong_schema_version(self, detection_result_v1_schema: dict) -> None:
        bad = {
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
        with pytest.raises(Exception):
            validate(instance=bad, schema=detection_result_v1_schema)

    def test_negative_people_count(self, detection_result_v1_schema: dict) -> None:
        bad = {
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
        with pytest.raises(Exception):
            validate(instance=bad, schema=detection_result_v1_schema)

    def test_negative_inference_ms(self, detection_result_v1_schema: dict) -> None:
        bad = {
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
        with pytest.raises(Exception):
            validate(instance=bad, schema=detection_result_v1_schema)
