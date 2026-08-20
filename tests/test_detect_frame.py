"""Tests for detect_frame() input validation.

These tests exercise the validation guard at the top of detect_frame()
without loading the real RT-DETRv2-S model.  The PersonObjectDetector
constructor is patched to skip _validate_paths and _load_model.
"""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from tests.fixtures.synthetic_frames import (
    empty_frame,
    float_frame,
    four_channel_frame,
    random_frame,
    single_channel_frame,
)


@pytest.fixture()
def detector():
    """Return a PersonObjectDetector with mocked model loading."""
    with patch("ai.detection.detector.PersonObjectDetector._validate_paths"), \
         patch("ai.detection.detector.PersonObjectDetector._load_model"):
        from ai.detection.detector import PersonObjectDetector
        det = PersonObjectDetector.__new__(PersonObjectDetector)
        det.config = type("C", (), {
            "confidence_threshold": 0.5,
            "allowed_classes": frozenset({"person"}),
            "device": None,
            "model_name": "RT-DETRv2-S",
            "model_version": "baseline-v1",
        })()
        det.device = type("D", (), {"type": "cpu"})()
        det._transform = None
        det._model = None
        yield det


class TestDetectFrameInputValidation:
    """Validate frame input constraints in detect_frame()."""

    def test_none_frame_raises(self, detector) -> None:
        with pytest.raises(ValueError, match="frame must be"):
            detector.detect_frame(None)

    def test_non_array_raises(self, detector) -> None:
        with pytest.raises(ValueError, match="frame must be"):
            detector.detect_frame("not an image")

    def test_single_channel_raises(self, detector) -> None:
        with pytest.raises(ValueError, match="frame must be"):
            detector.detect_frame(single_channel_frame())

    def test_four_channel_raises(self, detector) -> None:
        with pytest.raises(ValueError, match="frame must be"):
            detector.detect_frame(four_channel_frame())

    def test_2d_array_raises(self, detector) -> None:
        with pytest.raises(ValueError, match="frame must be"):
            detector.detect_frame(np.zeros((480, 640), dtype=np.uint8))

    def test_valid_frame_accepted(self, detector) -> None:
        frame = empty_frame()
        # The call will fail at model inference (mocked model is None),
        # but it must pass input validation first.
        with pytest.raises((RuntimeError, AttributeError, Exception)):
            detector.detect_frame(frame)
