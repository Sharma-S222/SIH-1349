"""Tests for FileVideoSource."""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import tempfile

import cv2
import numpy as np
import pytest

from integration.video.sources import FileVideoSource
from integration.video.types import ConnectionStatus


def create_test_video(path: str, width: int = 320, height: int = 240, frames: int = 50):
    """Create a tiny test video programmatically."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 30.0, (width, height))
    for i in range(frames):
        img = np.full((height, width, 3), fill_value=i % 256, dtype=np.uint8)
        writer.write(img)
    writer.release()


@pytest.fixture
def test_video(tmp_path):
    path = str(tmp_path / "test_input.mp4")
    create_test_video(path)
    return path


class TestFileVideoSource:
    def test_open_and_read(self, test_video):
        src = FileVideoSource("CAM_TEST", test_video)
        assert src.open() is True
        assert src.is_open() is True

        frame = src.read()
        assert frame is not None
        assert frame.camera_id == "CAM_TEST"
        assert frame.frame_index == 1
        assert frame.width == 320
        assert frame.height == 240
        assert frame.frame.dtype == np.uint8
        assert frame.frame.shape == (240, 320, 3)
        assert frame.source_type == "file"

        src.close()
        assert src.is_open() is False
        assert src.state.connection_status == ConnectionStatus.DISCONNECTED

    def test_frame_index_monotonic(self, test_video):
        src = FileVideoSource("CAM_TEST", test_video)
        src.open()

        indices = []
        while True:
            f = src.read()
            if f is None:
                break
            indices.append(f.frame_index)

        src.close()
        assert indices == list(range(1, len(indices) + 1))

    def test_timestamp_monotonic(self, test_video):
        src = FileVideoSource("CAM_TEST", test_video)
        src.open()

        timestamps = []
        while True:
            f = src.read()
            if f is None:
                break
            timestamps.append(f.timestamp_ms)

        src.close()
        assert timestamps == sorted(timestamps)

    def test_eof_returns_none(self, test_video):
        src = FileVideoSource("CAM_TEST", test_video)
        src.open()
        for _ in range(100):
            src.read()
        # After all frames, should return None
        assert src.read() is None
        src.close()

    def test_invalid_file(self):
        src = FileVideoSource("CAM_TEST", "/nonexistent/path/video.mp4")
        assert src.open() is False
        assert src.state.connection_status == ConnectionStatus.ERROR

    def test_metadata(self, test_video):
        src = FileVideoSource("CAM_TEST", test_video)
        src.open()
        meta = src.get_metadata()
        assert meta.camera_id == "CAM_TEST"
        assert meta.source_type == "file"
        assert meta.width == 320
        assert meta.height == 240
        assert meta.fps == 30.0
        src.close()
