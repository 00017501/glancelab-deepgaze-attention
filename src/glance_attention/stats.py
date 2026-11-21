"""AOI statistics over a fixation density map (definitions in docs/METHOD.md section 4)."""

import numpy as np
import numpy.typing as npt

from src.glance_attention.schemas import REST_AOI_NAME, Aoi, AoiRow, AoiType, Box, CenterBias, SummaryRow

type Density = npt.NDArray[np.float64]
type Mask = npt.NDArray[np.bool_]

# Pooling block for the entropy; 10 px keeps single-pixel noise from inflating the entropy.
ENTROPY_GRID_PX = 10
# Fraction of most-attended pixels used by the top-share focus measure.
TOP_PIXEL_FRACTION = 0.10
# Peak density is scaled by 1e6 so the table shows readable numbers.
PEAK_SCALE = 1e6


def aoi_mask(boxes: list[Box], height: int, width: int) -> Mask:
    """Return a boolean mask of the union of `boxes`, clipped to the image."""
    mask = np.zeros((height, width), bool)
    for x0, y0, x1, y1 in boxes:
        mask[max(0, int(y0)) : min(height, int(y1)), max(0, int(x0)) : min(width, int(x1))] = True
    return mask


def exclusive_masks(aois: dict[str, Aoi], priority: list[str], height: int, width: int) -> dict[str, Mask]:
    """Return one mask per AOI in file order, then the rest; every pixel belongs to exactly one mask.

    AOIs named in `priority` claim their pixels first, in that order; the others follow in file order.
    """
    order = [name for name in priority if name in aois] + [name for name in aois if name not in priority]
    claimed = np.zeros((height, width), bool)
    masks = {}
    for name in order:
        masks[name] = aoi_mask(aois[name].boxes, height, width) & ~claimed
        claimed |= masks[name]
    return {**{name: masks[name] for name in aois}, REST_AOI_NAME: ~claimed}


def entropy_norm(density: Density) -> float:
    """Return the Shannon entropy of the grid-pooled density divided by its maximum; 0..1, lower = more focused."""
    height, width = density.shape
    cropped_h, cropped_w = height // ENTROPY_GRID_PX * ENTROPY_GRID_PX, width // ENTROPY_GRID_PX * ENTROPY_GRID_PX
    cells = (
        density[:cropped_h, :cropped_w]
        .reshape(cropped_h // ENTROPY_GRID_PX, ENTROPY_GRID_PX, cropped_w // ENTROPY_GRID_PX, ENTROPY_GRID_PX)
        .sum(axis=(1, 3))
        .ravel()
    )
    cells = cells / cells.sum()
    nonzero = cells[cells > 0]
    return float(-(nonzero * np.log(nonzero)).sum() / np.log(cells.size))


def top_k_share(density: Density, fraction: float = TOP_PIXEL_FRACTION) -> float:
    """Return the share (0..1) of attention falling in the `fraction` most-attended pixels."""
    flat = np.sort(density.ravel())[::-1]
    k = max(1, int(len(flat) * fraction))
    return float(flat[:k].sum() / flat.sum())


def aoi_shares(masks: dict[str, Mask], density: Density) -> dict[str, float]:
    """Return the % of attention inside each mask."""
    return {name: float(100 * density[mask].sum()) for name, mask in masks.items()}


def _rank(rows: list[AoiRow], field: str) -> dict[str, int]:
    """Return 1-based ranks of the drawn AOIs by `field`, highest first; ties keep file order."""
    drawn = [row for row in rows if row.aoi != REST_AOI_NAME]
    return {row.aoi: rank for rank, row in enumerate(sorted(drawn, key=lambda row: -getattr(row, field)), 1)}


def compute_rows(
    labels: tuple[str, CenterBias], aois: dict[str, Aoi], priority: list[str], density: Density
) -> tuple[list[AoiRow], SummaryRow]:
    """Return per-AOI rows (rest last) and the whole-image summary for one `(variant, prior)` density."""
    variant, centerbias = labels
    masks = exclusive_masks(aois, priority, *density.shape)
    rows = []
    for name, mask in masks.items():
        share_pct, area_pct = float(100 * density[mask].sum()), float(100 * mask.mean())
        rows.append(
            AoiRow(
                variant=variant,
                centerbias=centerbias,
                aoi=name,
                type=aois[name].type if name in aois else AoiType.REST,
                share_pct=share_pct,
                area_pct=area_pct,
                density=share_pct / area_pct if area_pct else 0.0,
                peak=float(PEAK_SCALE * density[mask].max()) if mask.any() else 0.0,
            )
        )
    share_ranks, look_ranks = _rank(rows, "share_pct"), _rank(rows, "peak")
    for row in rows:
        row.share_rank, row.first_look_rank = share_ranks.get(row.aoi), look_ranks.get(row.aoi)
    entropy = entropy_norm(density)
    summary = SummaryRow(
        variant=variant,
        centerbias=centerbias,
        entropy_norm=entropy,
        clarity=1 - entropy,
        top10_pct=100 * top_k_share(density),
        first_look_order=" > ".join(sorted(look_ranks, key=look_ranks.__getitem__)),
    )
    return rows, summary
