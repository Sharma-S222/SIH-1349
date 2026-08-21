"""Camera configuration for the SIH1349 video runtime."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml


class SourceType(Enum):
    FILE = "file"
    WEBCAM = "webcam"
    RTSP = "rtsp"


@dataclass
class CameraConfig:
    """Validated camera configuration."""

    camera_id: str
    enabled: bool
    source_type: SourceType
    source_uri: Optional[str]
    device_index: int = 0
    analysis_every_n_frames: int = 3
    queue_size: int = 3
    reconnect_enabled: bool = True
    reconnect_initial_delay_ms: int = 1000
    reconnect_max_delay_ms: int = 30000
    reconnect_max_attempts: int = 0

    def validate(self):
        if not self.camera_id or not self.camera_id.strip():
            raise ValueError("camera_id must be non-empty")
        if self.enabled and self.source_uri is None:
            raise ValueError(f"{self.camera_id}: enabled but source_uri is None")
        if self.analysis_every_n_frames < 1:
            raise ValueError(f"{self.camera_id}: analysis_every_n_frames must be >= 1")
        if self.queue_size < 1:
            raise ValueError(f"{self.camera_id}: queue_size must be >= 1")


def load_camera_config(yaml_input) -> List[CameraConfig]:
    """Load and validate camera configuration from a YAML string or dict.

    Args:
        yaml_input: YAML string, file path, or dict.

    Returns:
        List of validated CameraConfig objects.

    Raises:
        ValueError: On validation errors (duplicates, missing fields, etc.).
    """
    if isinstance(yaml_input, str) and not yaml_input.strip().startswith("{"):
        # Could be a file path or YAML string
        import os
        if os.path.isfile(yaml_input):
            with open(yaml_input, "r") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(yaml_input)
    elif isinstance(yaml_input, dict):
        data = yaml_input
    else:
        data = yaml.safe_load(yaml_input)

    cameras_data = data.get("cameras", [])
    configs = []
    seen_ids = set()

    for cam in cameras_data:
        cam_id = cam.get("camera_id", "")
        if cam_id in seen_ids:
            raise ValueError(f"Duplicate camera_id: {cam_id}")
        seen_ids.add(cam_id)

        source_type_str = cam.get("source_type", "file")
        try:
            source_type = SourceType(source_type_str)
        except ValueError:
            raise ValueError(
                f"{cam_id}: invalid source_type '{source_type_str}'. "
                f"Must be one of: {[s.value for s in SourceType]}"
            )

        cfg = CameraConfig(
            camera_id=cam_id,
            enabled=cam.get("enabled", False),
            source_type=source_type,
            source_uri=cam.get("source_uri"),
            device_index=cam.get("device_index", 0),
            analysis_every_n_frames=cam.get("analysis_every_n_frames", 3),
            queue_size=cam.get("queue_size", 3),
            reconnect_enabled=cam.get("reconnect_enabled", True),
            reconnect_initial_delay_ms=cam.get("reconnect_initial_delay_ms", 1000),
            reconnect_max_delay_ms=cam.get("reconnect_max_delay_ms", 30000),
            reconnect_max_attempts=cam.get("reconnect_max_attempts", 0),
        )
        cfg.validate()
        configs.append(cfg)

    return configs
