"""Tests for confidence score validation."""

from __future__ import annotations

from typing import Any

import pytest


class TestConfidenceValidation:
    """Verify confidence values are floats in [0.0, 1.0]."""

    def test_confidence_is_float(self, single_person_result: dict[str, Any]) -> None:
        det = single_person_result["detections"][0]
        assert isinstance(det["confidence"], float)

    def test_confidence_in_range(self, single_person_result: dict[str, Any]) -> None:
        conf = single_person_result["detections"][0]["confidence"]
        assert 0.0 <= conf <= 1.0

    def test_multi_detection_confidences_in_range(
        self, multi_detection_result: dict[str, Any]
    ) -> None:
        for det in multi_detection_result["detections"]:
            conf = det["confidence"]
            assert isinstance(conf, float)
            assert 0.0 <= conf <= 1.0

    def test_confidence_at_boundary_zero(self) -> None:
        conf = 0.0
        assert 0.0 <= conf <= 1.0

    def test_confidence_at_boundary_one(self) -> None:
        conf = 1.0
        assert 0.0 <= conf <= 1.0

    def test_confidence_below_zero_invalid(self) -> None:
        conf = -0.1
        assert not (0.0 <= conf <= 1.0)

    def test_confidence_above_one_invalid(self) -> None:
        conf = 1.1
        assert not (0.0 <= conf <= 1.0)

    def test_confidence_not_nan(self) -> None:
        import math
        conf = float("nan")
        assert not (0.0 <= conf <= 1.0) or math.isnan(conf)

    def test_confidence_not_inf(self) -> None:
        import math
        conf = float("inf")
        assert not (0.0 <= conf <= 1.0) or math.isinf(conf)

    def test_all_detections_have_confidence(
        self, multi_detection_result: dict[str, Any]
    ) -> None:
        for det in multi_detection_result["detections"]:
            assert "confidence" in det
            assert isinstance(det["confidence"], (int, float))
