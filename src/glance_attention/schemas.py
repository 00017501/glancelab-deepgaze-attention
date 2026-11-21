"""Typed shapes for the per-variant AOI files and for every row written to disk."""

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

# Name of the computed AOI holding every pixel no drawn AOI covers.
REST_AOI_NAME = "rest"
# `aoi` value of rows that describe the whole image rather than one AOI.
IMAGE_LEVEL = "(image)"


class AoiType(StrEnum):
    """Category of an area of interest; drives the box colour in the overlays."""

    PRICE = "price"
    PRODUCT = "product"
    LOGO = "logo"
    HEADLINE = "headline"
    TEXT = "text"
    VISUAL = "visual"
    REST = "rest"


class CenterBias(StrEnum):
    """Prior given to the model: the standard MIT1003 centre bias, or none (uniform)."""

    MIT1003 = "mit1003"
    UNIFORM = "uniform"


type Box = tuple[int, int, int, int]


class Aoi(BaseModel):
    """One area of interest: a type and one or more `[x0, y0, x1, y1]` pixel boxes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: AoiType
    boxes: list[Box] = Field(min_length=1)


class VariantAois(BaseModel):
    """The AOI file of one variant: its image file name and its AOIs in drawing order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    image: str
    aois: dict[str, Aoi]


class AoiRow(BaseModel):
    """One row of `<variant>_aoi.csv`; field order is the CSV column order."""

    variant: str
    centerbias: CenterBias
    aoi: str
    type: AoiType
    share_pct: float
    area_pct: float
    density: float
    peak: float
    share_rank: int | None = None
    first_look_rank: int | None = None


class SummaryRow(BaseModel):
    """One row of `summary.csv`: whole-image measures for one variant under one prior."""

    variant: str
    centerbias: CenterBias
    entropy_norm: float
    clarity: float
    top10_pct: float
    first_look_order: str


class CompareRow(BaseModel):
    """One row of `compare.csv`: one metric of one AOI, baseline against a variant."""

    variant: str
    baseline: str
    centerbias: CenterBias
    aoi: str
    metric: str
    baseline_value: float | None
    variant_value: float | None
    delta: float | None
    delta_rel_pct: float | None


class VerdictRow(BaseModel):
    """One row of `verdict.csv`: the key test for one variant against the baseline."""

    variant: str
    baseline: str
    centerbias: CenterBias
    price_share_pct: float
    price_delta_pp: float
    is_price_up: bool
    product_share_pct: float
    product_delta_rel_pct: float
    product_density_delta_rel_pct: float
    threshold_pct: float
    is_product_held: bool
    verdict: str


class JitterRow(BaseModel):
    """One row of `jitter.csv`: how an AOI's share moves when every box is redrawn slightly off."""

    variant: str
    centerbias: CenterBias
    aoi: str
    share_pct: float
    jitter_mean: float
    jitter_sd: float
    jitter_min: float
    jitter_max: float
    draws: int


class StabilityRow(BaseModel):
    """One row of `jitter_stability.csv`: how often a conclusion survives the jittered boxes."""

    centerbias: CenterBias
    check: str
    unchanged_pct: float
    draws: int


class LongRow(BaseModel):
    """One row of the cross-tool table; the columns are shared with the other attention tools."""

    tool: str
    variant: str
    aoi: str
    metric: str
    value: float | str | None
    scale: str
    run_date: str
    version: str


def load_aois(path: Path) -> VariantAois:
    """Load and validate one AOI file; top-level keys starting with `_` are notes and are skipped."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return VariantAois.model_validate({key: value for key, value in raw.items() if not key.startswith("_")})
