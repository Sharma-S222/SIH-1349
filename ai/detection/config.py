"""Configuration for detector backends (RF-DETR Medium / RT-DETRv2-S fallback)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_RFDETR_WEIGHTS = Path.home() / ".roboflow" / "models" / "rf-detr-medium.pth"


@dataclass(frozen=True)
class DetectorConfig:
    """Runtime settings kept outside the detector's core logic."""

    confidence_threshold: float = 0.50
    allowed_classes: FrozenSet[str] = field(
        default_factory=lambda: frozenset({"person", "backpack", "handbag", "suitcase"})
    )
    device: Optional[str] = None

    # RF-DETR Medium (primary detector)
    model_name: str = "RF-DETR-Medium"
    model_version: str = "rf-detr-medium-v1"
    rf_detr_weights_path: Path = _DEFAULT_RFDETR_WEIGHTS

    # RT-DETRv2-S (rollback fallback — kept for quick revert)
    rtdetr_weights_path: Path = PROJECT_ROOT / "weights" / "rtdetrv2_s.pth"
    rtdetr_model_root: Path = PROJECT_ROOT / "third_party" / "RT-DETR" / "rtdetrv2_pytorch"

    @property
    def model_config_path(self) -> Path:
        nested = self.rtdetr_model_root / "rtdetrv2_pytorch"
        if nested.is_dir():
            return nested / "configs" / "rtdetrv2" / "rtdetrv2_r18vd_120e_coco.yml"
        return self.rtdetr_model_root / "configs" / "rtdetrv2" / "rtdetrv2_r18vd_120e_coco.yml"
