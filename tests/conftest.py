"""Shared pytest fixtures for Member 1 detection tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tests.fixtures.synthetic_frames import empty_frame, random_frame, solid_frame

SCHEMA_PATH = Path(__file__).parent / "schemas" / "detection_result_v1.json"


@pytest.fixture()
def detection_result_v1_schema() -> dict[str, Any]:
    """Load the DetectionResult v1 JSON Schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def empty_detections_result() -> dict[str, Any]:
    """A valid DetectionResult with zero detections."""
    return {
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


@pytest.fixture()
def single_person_result() -> dict[str, Any]:
    """A valid DetectionResult with one person detection."""
    return {
        "schema_version": "detection-v1",
        "camera_id": "CAM_TEST",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_width": 640,
        "frame_height": 480,
        "people_count": 1,
        "detections": [
            {
                "detection_id": "det_1",
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.92,
                "bbox_xyxy": [100, 50, 300, 400],
            }
        ],
        "inference_ms": 150.0,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }


@pytest.fixture()
def multi_detection_result() -> dict[str, Any]:
    """A valid DetectionResult with mixed classes (persons + objects)."""
    return {
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
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.88,
                "bbox_xyxy": [500, 250, 750, 900],
            },
            {
                "detection_id": "det_3",
                "class_id": 24,
                "class_name": "backpack",
                "confidence": 0.72,
                "bbox_xyxy": [800, 400, 900, 600],
            },
        ],
        "inference_ms": 200.5,
        "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"},
    }


@pytest.fixture()
def synthetic_frame():
    """Return a deterministic random BGR frame (640x480)."""
    return random_frame(640, 480, seed=42)


@pytest.fixture()
def small_frame():
    """Return a small deterministic BGR frame (320x240)."""
    return random_frame(320, 240, seed=99)
"""Root conftest for SIH1349 tests."""
import sys
from pathlib import Path

# Add project root to sys.path so integration.video can be imported
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

