"""Tests for camera configuration."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from integration.video.config import CameraConfig, SourceType, load_camera_config


VALID_CONFIG = """
cameras:
  - camera_id: CAM_PLATFORM_01
    enabled: true
    source_type: file
    source_uri: ""
    analysis_every_n_frames: 3
    queue_size: 3
  - camera_id: CAM_ENTRY_01
    enabled: false
    source_type: rtsp
    source_uri: ""
    analysis_every_n_frames: 3
    queue_size: 3
"""

DUPLICATE_CONFIG = """
cameras:
  - camera_id: CAM_PLATFORM_01
    enabled: true
    source_type: file
    source_uri: ""
  - camera_id: CAM_PLATFORM_01
    enabled: false
    source_type: rtsp
    source_uri: ""
"""

INVALID_SOURCE_TYPE = """
cameras:
  - camera_id: CAM_BAD
    enabled: true
    source_type: submarine
    source_uri: ""
"""

INVALID_ANALYSIS_CADENCE = """
cameras:
  - camera_id: CAM_BAD
    enabled: true
    source_type: file
    source_uri: ""
    analysis_every_n_frames: 0
"""


class TestLoadCameraConfig:
    def test_valid_config(self):
        configs = load_camera_config(VALID_CONFIG)
        assert len(configs) == 2
        assert configs[0].camera_id == "CAM_PLATFORM_01"
        assert configs[0].enabled is True
        assert configs[0].source_type == SourceType.FILE
        assert configs[1].camera_id == "CAM_ENTRY_01"
        assert configs[1].enabled is False

    def test_duplicate_rejected(self):
        with pytest.raises(ValueError, match="Duplicate camera_id"):
            load_camera_config(DUPLICATE_CONFIG)

    def test_invalid_source_type(self):
        with pytest.raises(ValueError, match="invalid source_type"):
            load_camera_config(INVALID_SOURCE_TYPE)

    def test_invalid_analysis_cadence(self):
        with pytest.raises(ValueError, match="analysis_every_n_frames must be >= 1"):
            load_camera_config(INVALID_ANALYSIS_CADENCE)


class TestCameraConfig:
    def test_validate_empty_id(self):
        cfg = CameraConfig(
            camera_id="",
            enabled=True,
            source_type=SourceType.FILE,
            source_uri="test.mp4",
        )
        with pytest.raises(ValueError, match="camera_id must be non-empty"):
            cfg.validate()

    def test_validate_enabled_no_uri(self):
        cfg = CameraConfig(
            camera_id="CAM_TEST",
            enabled=True,
            source_type=SourceType.FILE,
            source_uri=None,
        )
        with pytest.raises(ValueError, match="enabled but source_uri is None"):
            cfg.validate()

    def test_validate_disabled_no_uri_ok(self):
        cfg = CameraConfig(
            camera_id="CAM_TEST",
            enabled=False,
            source_type=SourceType.RTSP,
            source_uri=None,
        )
        cfg.validate()  # Should not raise
