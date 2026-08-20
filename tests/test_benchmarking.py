"""Phase 9: Benchmarking for PersonObjectDetector.

Tests the detector's performance characteristics including:
- Inference latency (inference_ms)
- Frames per second (FPS) measurement
- Consistent timing across multiple runs

These tests verify the detector's timing characteristics are
consistent and reasonable.
"""

from __future__ import annotations

import time
import numpy as np
from pathlib import Path

# Add project root to path
sys_path = str(Path(__file__).resolve().parent.parent)
if sys_path not in Path.__dict__.get('_projects', []):
    pass

from ai.detection.detector import PersonObjectDetector
from ai.detection.config import DetectorConfig


def _make_detector() -> PersonObjectDetector:
    """Helper to create a detector instance."""
    config = DetectorConfig()
    return PersonObjectDetector(config)


def _make_frame(
    width: int = 640, height: int = 480, seed: int = 42
) -> np.ndarray:
    """Helper to create a deterministic random BGR frame."""
    rng = np.random.RandomState(seed)
    return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)


class TestBenchmarkLatency:
    """Test that inference latency is reasonable and consistent."""

    def test_inference_ms_is_positive(self) -> None:
        """Test that inference_ms is always positive after a run.

        Verifies the detector records positive inference time.
        """
        detector = _make_detector()
        frame = _make_frame(seed=42)
        result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)
        assert result["inference_ms"] > 0, "inference_ms should be positive"
        assert isinstance(result["inference_ms"], float), \
            "inference_ms should be a float"

    def test_inference_ms_reasonable_range(self) -> None:
        """Test that inference_ms is in a reasonable range.

        Verifies inference time is neither too fast (probably
        measurements too coarse) nor too slow (probably blocking).
        """
        detector = _make_detector()
        frame = _make_frame(seed=42)
        result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)
        # Should be well above 0 and below, say, 5 seconds
        assert 0 < result["inference_ms"] < 5000, \
            f"inference_ms {result['inference_ms']} is outside reasonable range"

    def test_multiple_runs_consistent(self) -> None:
        """Test that inference time is relatively consistent across runs.

        Runs the detector multiple times on the same frame and
        verifies inference times are within a reasonable factor
        of each other.
        """
        detector = _make_detector()
        frame = _make_frame(seed=42)
        times = []
        for _ in range(5):
            import time as time_module
            start = time_module.perf_counter()
            result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)
            end = time_module.perf_counter()
            times.append(result["inference_ms"])

        # All times should be positive
        assert all(t > 0 for t in times), "All inference times should be positive"
        # Times should not vary by more than 10x
        max_time = max(times)
        min_time = min(times)
        assert max_time < min_time * 10, \
            f"Inference times vary too much: {times}"


class TestFpsMeasurement:
    """Test FPS measurement over multiple frames."""

    def test_fps_over_multiple_frames(self) -> None:
        """Test FPS calculation over a sequence of frames.

        Runs the detector on multiple frames and verifies
        FPS can be calculated and is positive.
        """
        detector = _make_detector()
        frame = _make_frame(seed=42)

        # Run 10 frames and measure total time
        import time as time_module
        start = time_module.perf_counter()
        for _ in range(10):
            detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)
        end = time_module.perf_counter()

        total_ms = (end - start) * 1000
        fps = 10000 / total_ms  # 10 frames in milliseconds, scaled

        # FPS should be positive
        assert fps > 0, "FPS should be positive"
        # FPS should be reasonable (at least 0.1 FPS, at most 100 FPS)
        assert 0.1 < fps < 100, f"FPS {fps} is outside reasonable range"

    def test_single_frame_inference_time(self) -> None:
        """Test single frame inference time is recorded correctly.

        Verifies that a single frame run records inference_ms
        and it's consistent with measured time.
        """
        detector = _make_detector()
        frame = _make_frame(seed=42)

        import time as time_module
        start = time_module.perf_counter()
        result = detector.detect_frame(frame, camera_id="CAM_01", frame_index=0)
        end = time_module.perf_counter()

        single_ms = (end - start) * 1000
        # The recorded inference_ms should be close to the measured time
        assert result["inference_ms"] > 0, "inference_ms should be positive"
        # Allow reasonable variation
        assert abs(result["inference_ms"] - single_ms) < 500, \
            f"Recorded inference_ms {result['inference_ms']} " \
            "differs too much from measured time {single_ms}"