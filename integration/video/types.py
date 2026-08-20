"""Core data types for the SIH1349 video runtime."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class Frame:
    """Internal frame contract — never serialized to JSON."""

    camera_id: str
    frame_index: int
    timestamp_ms: float
    frame: np.ndarray  # uint8, HxWx3, BGR
    width: int
    height: int
    source_type: str

    def __post_init__(self):
        assert self.frame.dtype == np.uint8, f"Frame dtype must be uint8, got {self.frame.dtype}"
        assert self.frame.ndim == 3 and self.frame.shape[2] == 3, (
            f"Frame must be HxWx3, got {self.frame.shape}"
        )


@dataclass
class SourceMetadata:
    """Lightweight source metadata — no credentials."""

    camera_id: str
    source_type: str
    width: int
    height: int
    fps: float
    status: ConnectionStatus
    codec: Optional[str] = None
    source_name: Optional[str] = None


@dataclass
class CameraState:
    """Per-camera runtime state — keyed by camera_id."""

    camera_id: str
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    frame_index: int = 0
    last_timestamp_ms: float = 0.0
    frames_received: int = 0
    frames_skipped: int = 0
    last_error: Optional[str] = None

    def record_frame(self, timestamp_ms: Optional[float] = None):
        self.frame_index += 1
        self.frames_received += 1
        self.last_timestamp_ms = timestamp_ms or (time.time() * 1000)

    def record_skip(self):
        self.frames_skipped += 1

    def set_error(self, error: str):
        self.connection_status = ConnectionStatus.ERROR
        self.last_error = error

    def set_connected(self):
        self.connection_status = ConnectionStatus.CONNECTED
        self.last_error = None

    def set_disconnected(self):
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_error = None

    def set_reconnecting(self):
        self.connection_status = ConnectionStatus.RECONNECTING
