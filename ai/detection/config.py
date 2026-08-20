"""Configuration for RT-DETRv2-S frame inference."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DetectorConfig:
    """Runtime settings kept outside the detector's core logic."""

    confidence_threshold: float = 0.50
    allowed_classes: FrozenSet[str] = field(
        default_factory=lambda: frozenset({"person", "backpack", "handbag", "suitcase"})
    )
    device: Optional[str] = None
    model_name: str = "RT-DETRv2-S"
    model_version: str = "baseline-v1"
    weights_path: Path = PROJECT_ROOT / "weights" / "rtdetrv2_s.pth"
    model_root: Path = PROJECT_ROOT / "third_party" / "RT-DETR" / "rtdetrv2_pytorch"

    @property
    def model_config_path(self) -> Path:
        return self.model_root / "configs" / "rtdetrv2" / "rtdetrv2_r18vd_120e_coco.yml"
