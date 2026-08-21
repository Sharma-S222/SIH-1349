"""Camera manager for the SIH1349 video runtime."""
from __future__ import annotations

import logging
import queue
import threading
from typing import Dict, List, Optional

from integration.video.config import CameraConfig, SourceType
from integration.video.sources import (
    FileVideoSource,
    RTSPVideoSource,
    VideoSource,
    WebcamVideoSource,
)
from integration.video.types import CameraState, ConnectionStatus, Frame

logger = logging.getLogger(__name__)


class CameraRuntime:
    """Manages one camera's decode thread and bounded queue."""

    def __init__(self, config: CameraConfig):
        self.config = config
        self.source: Optional[VideoSource] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=config.queue_size)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._frames_sent = 0
        self._frames_dropped = 0

    def start(self) -> bool:
        """Open source and start decode thread. Returns True on success."""
        self.source = self._create_source()
        if not self.source.open():
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._producer_loop,
            daemon=True,
            name=f"decode-{self.config.camera_id}",
        )
        self._thread.start()
        return True

    def _create_source(self) -> VideoSource:
        if self.config.source_type == SourceType.FILE:
            return FileVideoSource(
                self.config.camera_id, self.config.source_uri
            )
        elif self.config.source_type == SourceType.WEBCAM:
            return WebcamVideoSource(
                self.config.camera_id, self.config.device_index
            )
        elif self.config.source_type == SourceType.RTSP:
            return RTSPVideoSource(
                self.config.camera_id,
                self.config.source_uri,
                reconnect_enabled=self.config.reconnect_enabled,
                reconnect_initial_delay_ms=self.config.reconnect_initial_delay_ms,
                reconnect_max_delay_ms=self.config.reconnect_max_delay_ms,
                reconnect_max_attempts=self.config.reconnect_max_attempts,
            )
        else:
            raise ValueError(f"Unknown source_type: {self.config.source_type}")

    def _producer_loop(self):
        while self._running:
            frame = self.source.read()
            if frame is None:
                break
            try:
                self.frame_queue.put(frame, timeout=1.0)
                self._frames_sent += 1
            except queue.Full:
                self._frames_dropped += 1
                self.source.state.record_skip()

    def get_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        """Stop decode thread and close source."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        if self.source:
            self.source.close()

    @property
    def state(self) -> CameraState:
        if self.source:
            return self.source.state
        return CameraState(camera_id=self.config.camera_id)

    @property
    def frames_sent(self) -> int:
        return self._frames_sent

    @property
    def frames_dropped(self) -> int:
        return self._frames_dropped

    @property
    def queue_depth(self) -> int:
        return self.frame_queue.qsize()


class CameraManager:
    """Owns multiple CameraRuntimes keyed by camera_id.

    MVP execution: ONE ACTIVE CAMERA (CAM_PLATFORM_01).
    Architecture: multi-camera-ready.
    """

    def __init__(self, configs: List[CameraConfig]):
        self._runtimes: Dict[str, CameraRuntime] = {}
        self._configs = configs
        for cfg in configs:
            self._runtimes[cfg.camera_id] = CameraRuntime(cfg)

    def start_all(self) -> Dict[str, Optional[bool]]:
        """Start all enabled cameras. Returns {camera_id: started_or_disabled}."""
        results = {}
        for cam_id, runtime in self._runtimes.items():
            if runtime.config.enabled:
                ok = runtime.start()
                results[cam_id] = ok
                if ok:
                    logger.info(f"[{cam_id}] Started successfully")
                else:
                    logger.warning(f"[{cam_id}] Failed to start")
            else:
                results[cam_id] = None
                logger.info(f"[{cam_id}] Disabled, skipped")
        return results

    def get_frame(self, cam_id: str, timeout: float = 1.0) -> Optional[Frame]:
        return self._runtimes[cam_id].get_frame(timeout=timeout)

    def get_state(self, cam_id: str) -> CameraState:
        return self._runtimes[cam_id].state

    def get_runtime(self, cam_id: str) -> CameraRuntime:
        return self._runtimes[cam_id]

    def stop_all(self):
        for runtime in self._runtimes.values():
            runtime.stop()
