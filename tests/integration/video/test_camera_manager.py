"""Tests for CameraManager."""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import cv2
import numpy as np
import pytest

from integration.video.camera_manager import CameraManager, CameraRuntime
from integration.video.config import CameraConfig, SourceType, load_camera_config
from integration.video.types import ConnectionStatus


def create_test_video(path: str, width: int = 320, height: int = 240, frames: int = 50):
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


VALID_CONFIG_TEMPLATE = """
cameras:
  - camera_id: CAM_PLATFORM_01
    enabled: true
    source_type: file
    source_uri: "{path}"
    analysis_every_n_frames: 3
    queue_size: 3
  - camera_id: CAM_ENTRY_01
    enabled: false
    source_type: rtsp
    source_uri: ""
    analysis_every_n_frames: 3
    queue_size: 3
"""


class TestCameraManager:
    def test_single_camera_execution(self, test_video):
        config_yaml = VALID_CONFIG_TEMPLATE.format(path=test_video.replace("\\", "/"))
        configs = load_camera_config(config_yaml)
        mgr = CameraManager(configs)

        results = mgr.start_all()
        assert results["CAM_PLATFORM_01"] is True
        assert results["CAM_ENTRY_01"] is None  # disabled

        frames_read = 0
        while True:
            f = mgr.get_frame("CAM_PLATFORM_01", timeout=2.0)
            if f is None:
                break
            assert f.camera_id == "CAM_PLATFORM_01"
            frames_read += 1
            if frames_read >= 100:
                break

        state = mgr.get_state("CAM_PLATFORM_01")
        assert frames_read >= 10
        assert state.connection_status == ConnectionStatus.CONNECTED
        mgr.stop_all()
        assert mgr.get_state("CAM_PLATFORM_01").connection_status == ConnectionStatus.DISCONNECTED

    def test_disabled_camera_no_resources(self, test_video):
        config_yaml = VALID_CONFIG_TEMPLATE.format(path=test_video.replace("\\", "/"))
        configs = load_camera_config(config_yaml)
        mgr = CameraManager(configs)
        mgr.start_all()

        entry_rt = mgr.get_runtime("CAM_ENTRY_01")
        assert entry_rt.source is None
        assert entry_rt._running is False
        assert mgr.get_state("CAM_ENTRY_01").connection_status == ConnectionStatus.DISCONNECTED

        mgr.stop_all()

    def test_per_camera_state_isolation(self, test_video):
        config_yaml = VALID_CONFIG_TEMPLATE.format(path=test_video.replace("\\", "/"))
        configs = load_camera_config(config_yaml)
        mgr = CameraManager(configs)
        mgr.start_all()

        s1 = mgr.get_state("CAM_PLATFORM_01")
        s1.frames_received = 999

        s2 = mgr.get_state("CAM_ENTRY_01")
        assert s2.frames_received == 0
        assert s1.camera_id != s2.camera_id

        mgr.stop_all()

    def test_clean_shutdown(self, test_video):
        config_yaml = VALID_CONFIG_TEMPLATE.format(path=test_video.replace("\\", "/"))
        configs = load_camera_config(config_yaml)
        mgr = CameraManager(configs)
        mgr.start_all()

        for _ in range(20):
            mgr.get_frame("CAM_PLATFORM_01", timeout=1.0)

        mgr.stop_all()
        rt = mgr.get_runtime("CAM_PLATFORM_01")
        assert rt._running is False

    def test_queue_bounded(self, test_video):
        config_yaml = VALID_CONFIG_TEMPLATE.format(path=test_video.replace("\\", "/"))
        configs = load_camera_config(config_yaml)
        mgr = CameraManager(configs)
        mgr.start_all()

        rt = mgr.get_runtime("CAM_PLATFORM_01")
        assert rt.frame_queue.maxsize == 3

        mgr.stop_all()
