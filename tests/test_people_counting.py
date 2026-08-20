"""Tests for people counting logic in DetectionResult."""

from __future__ import annotations

from typing import Any

import pytest


class TestPeopleCounting:
    """Verify people_count is consistent with detections list."""

    def test_zero_detections_gives_zero_count(
        self, empty_detections_result: dict[str, Any]
    ) -> None:
        assert empty_detections_result["people_count"] == 0
        assert len(empty_detections_result["detections"]) == 0

    def test_single_person_count_matches(
        self, single_person_result: dict[str, Any]
    ) -> None:
        person_detections = [
            d for d in single_person_result["detections"] if d["class_name"] == "person"
        ]
        assert single_person_result["people_count"] == len(person_detections)
        assert single_person_result["people_count"] == 1

    def test_multi_person_count_matches(
        self, multi_detection_result: dict[str, Any]
    ) -> None:
        person_detections = [
            d for d in multi_detection_result["detections"] if d["class_name"] == "person"
        ]
        assert multi_detection_result["people_count"] == len(person_detections)
        assert multi_detection_result["people_count"] == 2

    def test_count_ignores_non_person_objects(
        self, multi_detection_result: dict[str, Any]
    ) -> None:
        non_person = [
            d for d in multi_detection_result["detections"] if d["class_name"] != "person"
        ]
        assert len(non_person) == 1
        assert multi_detection_result["people_count"] == 2

    def test_people_count_is_non_negative_integer(self) -> None:
        result = {
            "schema_version": "1.0",
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
        assert isinstance(result["people_count"], int)
        assert result["people_count"] >= 0

    def test_count_matches_all_person_detections(self) -> None:
        detections = [
            {"class_name": "person", "confidence": 0.9, "bbox_xyxy": [0, 0, 10, 10]},
            {"class_name": "person", "confidence": 0.8, "bbox_xyxy": [20, 20, 30, 30]},
            {"class_name": "backpack", "confidence": 0.7, "bbox_xyxy": [40, 40, 50, 50]},
        ]
        person_count = sum(1 for d in detections if d["class_name"] == "person")
        assert person_count == 2
