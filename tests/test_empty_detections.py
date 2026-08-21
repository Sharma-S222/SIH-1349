"""Tests for empty detection results."""

from __future__ import annotations

from typing import Any

import pytest


class TestEmptyDetections:
    """Verify correct behaviour when no objects are detected."""

    def test_empty_detections_is_list(
        self, empty_detections_result: dict[str, Any]
    ) -> None:
        assert isinstance(empty_detections_result["detections"], list)

    def test_empty_detections_length_zero(
        self, empty_detections_result: dict[str, Any]
    ) -> None:
        assert len(empty_detections_result["detections"]) == 0

    def test_empty_people_count_zero(
        self, empty_detections_result: dict[str, Any]
    ) -> None:
        assert empty_detections_result["people_count"] == 0

    def test_empty_schema_version(self, empty_detections_result: dict[str, Any]) -> None:
        assert empty_detections_result["schema_version"] == "detection-v1"

    def test_empty_frame_dimensions(
        self, empty_detections_result: dict[str, Any]
    ) -> None:
        assert empty_detections_result["frame_width"] == 640
        assert empty_detections_result["frame_height"] == 480

    def test_empty_inference_ms_non_negative(
        self, empty_detections_result: dict[str, Any]
    ) -> None:
        assert empty_detections_result["inference_ms"] >= 0

    def test_empty_model_info(self, empty_detections_result: dict[str, Any]) -> None:
        model = empty_detections_result["model"]
        assert model["name"] == "RT-DETRv2-S"
        assert model["version"] == "baseline-v1"
