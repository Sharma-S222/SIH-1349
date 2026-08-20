"""Public interface for the Member 1 detection module."""

from .config import DetectorConfig
from .detector import PersonObjectDetector

__all__ = ["DetectorConfig", "PersonObjectDetector"]
