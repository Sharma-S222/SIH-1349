"""Synthetic NumPy frame generators for deterministic unit tests."""

from __future__ import annotations

import numpy as np


def empty_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Return a black BGR frame with no objects."""
    return np.zeros((height, width, 3), dtype=np.uint8)


def solid_frame(
    color: tuple[int, int, int] = (128, 64, 32),
    width: int = 640,
    height: int = 480,
) -> np.ndarray:
    """Return a uniform-colour BGR frame."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = color
    return frame


def random_frame(width: int = 640, height: int = 480, seed: int = 42) -> np.ndarray:
    """Return a deterministic random-noise BGR frame."""
    rng = np.random.RandomState(seed)
    return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)


def single_channel_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Return a single-channel grayscale frame (invalid for detect_frame)."""
    return np.zeros((height, width), dtype=np.uint8)


def four_channel_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Return a 4-channel RGBA frame (invalid for detect_frame)."""
    return np.zeros((height, width, 4), dtype=np.uint8)


def float_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Return a float64 BGR frame (wrong dtype for detect_frame)."""
    return np.zeros((height, width, 3), dtype=np.float64)
