"""Video source implementations for the SIH1349 video runtime."""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

import cv2
import numpy as np

from integration.video.types import CameraState, ConnectionStatus, Frame, SourceMetadata

logger = logging.getLogger(__name__)


class VideoSource(ABC):
    """Abstract base for all video sources."""

    def __init__(self, camera_id: str, source_type: str):
        self.camera_id = camera_id
        self.source_type = source_type
        self.state = CameraState(camera_id=camera_id)

    @abstractmethod
    def open(self) -> bool:
        """Open the source. Returns True on success."""

    @abstractmethod
    def read(self) -> Optional[Frame]:
        """Read one frame. Returns None at EOF or on error."""

    @abstractmethod
    def is_open(self) -> bool:
        """Check if the source is currently open."""

    @abstractmethod
    def get_metadata(self) -> SourceMetadata:
        """Return source metadata."""

    @abstractmethod
    def close(self):
        """Release all resources."""


class FileVideoSource(VideoSource):
    """Read frames from a local video file (MP4, AVI, etc.)."""

    def __init__(self, camera_id: str, source_uri: str):
        super().__init__(camera_id, "file")
        self._source_uri = source_uri
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        self.state.set_connected()
        try:
            self._cap = cv2.VideoCapture(self._source_uri)
            if not self._cap.isOpened():
                self.state.set_error(f"Failed to open file: {self._source_uri}")
                return False
            self.state.set_connected()
            return True
        except Exception as e:
            self.state.set_error(str(e))
            return False

    def read(self) -> Optional[Frame]:
        if not self.is_open():
            return None
        ret, bgr = self._cap.read()
        if not ret:
            return None
        h, w = bgr.shape[:2]
        self.state.record_frame()
        return Frame(
            camera_id=self.camera_id,
            frame_index=self.state.frame_index,
            timestamp_ms=self.state.last_timestamp_ms,
            frame=bgr,
            width=w,
            height=h,
            source_type=self.source_type,
        )

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def get_metadata(self) -> SourceMetadata:
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if self._cap else 0
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if self._cap else 0
        fps = self._cap.get(cv2.CAP_PROP_FPS) if self._cap else 0.0
        return SourceMetadata(
            camera_id=self.camera_id,
            source_type=self.source_type,
            width=w,
            height=h,
            fps=fps,
            status=self.state.connection_status,
            source_name=self._source_uri,
        )

    def close(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        self.state.set_disconnected()


class WebcamVideoSource(VideoSource):
    """Read frames from a local webcam device."""

    def __init__(self, camera_id: str, device_index: int = 0):
        super().__init__(camera_id, "webcam")
        self._device_index = device_index
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        try:
            self._cap = cv2.VideoCapture(self._device_index)
            if not self._cap.isOpened():
                self.state.set_error(f"Failed to open webcam device {self._device_index}")
                return False
            self.state.set_connected()
            return True
        except Exception as e:
            self.state.set_error(str(e))
            return False

    def read(self) -> Optional[Frame]:
        if not self.is_open():
            return None
        ret, bgr = self._cap.read()
        if not ret:
            return None
        h, w = bgr.shape[:2]
        timestamp_ms = int(time.monotonic() * 1000)
        self.state.record_frame(timestamp_ms)
        return Frame(
            camera_id=self.camera_id,
            frame_index=self.state.frame_index,
            timestamp_ms=timestamp_ms,
            frame=bgr,
            width=w,
            height=h,
            source_type=self.source_type,
        )

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def get_metadata(self) -> SourceMetadata:
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if self._cap else 0
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if self._cap else 0
        fps = self._cap.get(cv2.CAP_PROP_FPS) if self._cap else 0.0
        return SourceMetadata(
            camera_id=self.camera_id,
            source_type=self.source_type,
            width=w,
            height=h,
            fps=fps,
            status=self.state.connection_status,
        )

    def close(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        self.state.set_disconnected()


class RTSPVideoSource(VideoSource):
    """Read frames from an RTSP stream with optional reconnection."""

    def __init__(
        self,
        camera_id: str,
        source_uri: str,
        reconnect_enabled: bool = True,
        reconnect_initial_delay_ms: int = 1000,
        reconnect_max_delay_ms: int = 30000,
        reconnect_max_attempts: int = 0,
    ):
        super().__init__(camera_id, "rtsp")
        self._source_uri = source_uri
        self._reconnect_enabled = reconnect_enabled
        self._reconnect_initial_delay_ms = reconnect_initial_delay_ms
        self._reconnect_max_delay_ms = reconnect_max_delay_ms
        self._reconnect_max_attempts = reconnect_max_attempts
        self._cap: Optional[cv2.VideoCapture] = None
        self._attempt = 0

    def _open_stream(self) -> bool:
        try:
            self._cap = cv2.VideoCapture(self._source_uri)
            if not self._cap.isOpened():
                return False
            return True
        except Exception:
            return False

    def open(self) -> bool:
        self.state.connection_status = ConnectionStatus.CONNECTING
        if self._open_stream():
            self.state.set_connected()
            self._attempt = 0
            return True
        self.state.set_error("Failed to open RTSP stream")
        return False

    def read(self) -> Optional[Frame]:
        if not self.is_open():
            if self._reconnect_enabled:
                return self._reconnect()
            return None

        ret, bgr = self._cap.read()
        if not ret:
            if self._reconnect_enabled:
                return self._reconnect()
            return None

        h, w = bgr.shape[:2]
        self.state.record_frame()
        self._attempt = 0
        return Frame(
            camera_id=self.camera_id,
            frame_index=self.state.frame_index,
            timestamp_ms=self.state.last_timestamp_ms,
            frame=bgr,
            width=w,
            height=h,
            source_type=self.source_type,
        )

    def _reconnect(self) -> Optional[Frame]:
        if self._reconnect_max_attempts > 0 and self._attempt >= self._reconnect_max_attempts:
            self.state.set_error("Max reconnect attempts reached")
            return None

        self.state.set_reconnecting()
        delay_s = min(
            self._reconnect_initial_delay_ms * (2 ** self._attempt),
            self._reconnect_max_delay_ms,
        ) / 1000.0
        logger.info(
            f"[{self.camera_id}] Reconnecting in {delay_s:.1f}s "
            f"(attempt {self._attempt + 1})"
        )
        time.sleep(delay_s)
        self._attempt += 1

        if self._cap:
            self._cap.release()
            self._cap = None

        if self._open_stream():
            self.state.set_connected()
            return self.read()

        self.state.set_error("Reconnect failed")
        return None

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def get_metadata(self) -> SourceMetadata:
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if self._cap else 0
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if self._cap else 0
        fps = self._cap.get(cv2.CAP_PROP_FPS) if self._cap else 0.0
        return SourceMetadata(
            camera_id=self.camera_id,
            source_type=self.source_type,
            width=w,
            height=h,
            fps=fps,
            status=self.state.connection_status,
            source_name=self._source_uri,
        )

    def close(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        self.state.set_disconnected()
