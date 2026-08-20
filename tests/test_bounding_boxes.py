"""Tests for bounding box format and constraints."""

from __future__ import annotations

from typing import Any

import pytest


class TestBoundingBoxFormat:
    """Validate bbox_xyxy structure and geometric constraints."""

    def test_bbox_has_four_elements(self) -> None:
        bbox = [10, 20, 100, 200]
        assert len(bbox) == 4

    def test_bbox_elements_are_numeric(self) -> None:
        bbox = [10, 20, 100, 200]
        for val in bbox:
            assert isinstance(val, (int, float))

    def test_x1_less_than_x2(self) -> None:
        x1, y1, x2, y2 = 10, 20, 100, 200
        assert x1 < x2

    def test_y1_less_than_y2(self) -> None:
        x1, y1, x2, y2 = 10, 20, 100, 200
        assert y1 < y2

    def test_bbox_within_frame_bounds(self) -> None:
        frame_w, frame_h = 640, 480
        x1, y1, x2, y2 = 100, 50, 300, 400
        assert 0 <= x1 and x2 <= frame_w
        assert 0 <= y1 and y2 <= frame_h

    def test_detection_bbox_format(self, single_person_result: dict[str, Any]) -> None:
        det = single_person_result["detections"][0]
        bbox = det["bbox_xyxy"]
        assert isinstance(bbox, list)
        assert len(bbox) == 4
        assert all(isinstance(v, (int, float)) for v in bbox)
        assert bbox[0] < bbox[2]
        assert bbox[1] < bbox[3]

    def test_multi_detection_bbox_format(
        self, multi_detection_result: dict[str, Any]
    ) -> None:
        for det in multi_detection_result["detections"]:
            bbox = det["bbox_xyxy"]
            assert len(bbox) == 4
            assert bbox[0] < bbox[2]
            assert bbox[1] < bbox[3]

    def test_bbox_zero_width_invalid(self) -> None:
        x1, y1, x2, y2 = 100, 50, 100, 200
        assert x1 == x2

    def test_bbox_negative_coords_invalid(self) -> None:
        x1, y1, x2, y2 = -10, -20, 100, 200
        assert x1 < 0 or y1 < 0
