"""Public interface for the Member 1 detection module."""

from .config import DetectorConfig
from .rf_detr_detector import PersonObjectDetector
from .detector import PersonObjectDetector as RTDETRDetector

__all__ = ["DetectorConfig", "PersonObjectDetector", "RTDETRDetector"]
