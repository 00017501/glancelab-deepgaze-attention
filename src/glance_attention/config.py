"""The study configuration read from `study.toml`; every setting has a default."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CONFIG_FILE_NAME = "study.toml"


class ExternalMetric(BaseModel):
    """One number another attention tool supplies, per AOI or per image, on that tool's own scale."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: str
    level: Literal["aoi", "image"] = "aoi"
    scale: str = ""


class ExternalTool(BaseModel):
    """Another attention tool whose hand-exported numbers go into the cross-tool table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    metrics: list[ExternalMetric]


def _default_tools() -> list[ExternalTool]:
    """Return the template used when `study.toml` lists no tools: attention % per AOI and a clarity score."""
    metrics = [
        ExternalMetric(metric="attention_pct", level="aoi", scale="0-100 % of attention"),
        ExternalMetric(metric="clarity_score", level="image", scale="0-100"),
    ]
    return [ExternalTool(name=name, metrics=metrics) for name in ("attention_insight", "neurons_predict")]


class StudyConfig(BaseModel):
    """Settings of one study; AOIs are referred to by the names used in the AOI files."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = "Untitled study"
    # Variant every other variant is compared against; the first variant by name when unset.
    baseline: str | None = None
    # The one AOI that moves between variants; every other AOI must be identical in all of them.
    moving_aoi: str = "price"
    product_aoi: str = "product"
    # AOIs listed here win overlapping pixels, in this order; unlisted AOIs follow in file order.
    aoi_priority: list[str] = ["price"]
    # A variant is flagged when its product share falls by more than this % of the baseline share.
    product_drop_threshold_pct: float = Field(default=10.0, ge=0)
    # Each box edge moves by up to this % of the box's width or height in the robustness check.
    jitter_pct: float = Field(default=5.0, ge=0)
    jitter_draws: int = Field(default=200, ge=1)
    jitter_seed: int = 20261122
    # True marks every output of the study as a placeholder, never to be reported.
    placeholder: bool = False
    centerbias_path: str = "centerbias_mit1003.npy"
    external_tools: list[ExternalTool] = Field(default_factory=_default_tools)


def load_config(study_root: Path) -> StudyConfig:
    """Load `study.toml` from the study folder; a missing file means all defaults."""
    path = study_root / CONFIG_FILE_NAME
    if not path.exists():
        return StudyConfig()
    return StudyConfig.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
