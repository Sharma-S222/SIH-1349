"""Tests for allowed class filtering logic."""

from __future__ import annotations

import pytest

ALLOWED_CLASSES = frozenset({"person", "backpack", "handbag", "suitcase"})


class TestClassFiltering:
    """Verify detection filtering by allowed_classes set."""

    def test_person_in_allowed(self) -> None:
        assert "person" in ALLOWED_CLASSES

    def test_backpack_in_allowed(self) -> None:
        assert "backpack" in ALLOWED_CLASSES

    def test_handbag_in_allowed(self) -> None:
        assert "handbag" in ALLOWED_CLASSES

    def test_suitcase_in_allowed(self) -> None:
        assert "suitcase" in ALLOWED_CLASSES

    def test_car_not_in_allowed(self) -> None:
        assert "car" not in ALLOWED_CLASSES

    def test_dog_not_in_allowed(self) -> None:
        assert "dog" not in ALLOWED_CLASSES

    def test_filtering_preserves_person(self) -> None:
        detections = [
            {"class_name": "person", "confidence": 0.9},
            {"class_name": "car", "confidence": 0.8},
            {"class_name": "person", "confidence": 0.7},
        ]
        filtered = [d for d in detections if d["class_name"] in ALLOWED_CLASSES]
        assert len(filtered) == 2
        assert all(d["class_name"] == "person" for d in filtered)

    def test_filtering_removes_disallowed(self) -> None:
        detections = [
            {"class_name": "car", "confidence": 0.9},
            {"class_name": "dog", "confidence": 0.8},
            {"class_name": "truck", "confidence": 0.7},
        ]
        filtered = [d for d in detections if d["class_name"] in ALLOWED_CLASSES]
        assert len(filtered) == 0

    def test_filtering_mixed_classes(self) -> None:
        detections = [
            {"class_name": "person", "confidence": 0.95},
            {"class_name": "backpack", "confidence": 0.72},
            {"class_name": "car", "confidence": 0.88},
            {"class_name": "handbag", "confidence": 0.65},
            {"class_name": "suitcase", "confidence": 0.55},
            {"class_name": "dog", "confidence": 0.45},
        ]
        filtered = [d for d in detections if d["class_name"] in ALLOWED_CLASSES]
        names = {d["class_name"] for d in filtered}
        assert names == {"person", "backpack", "handbag", "suitcase"}

    def test_confidence_filter_combined(self) -> None:
        threshold = 0.50
        detections = [
            {"class_name": "person", "confidence": 0.95},
            {"class_name": "person", "confidence": 0.30},
            {"class_name": "car", "confidence": 0.80},
        ]
        filtered = [
            d for d in detections
            if d["class_name"] in ALLOWED_CLASSES and d["confidence"] >= threshold
        ]
        assert len(filtered) == 1
        assert filtered[0]["class_name"] == "person"
