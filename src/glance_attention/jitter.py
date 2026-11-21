"""Robustness check: redraw every AOI box slightly off, many times, and see how far the shares move."""

import numpy as np

from src.glance_attention.compare import is_product_held
from src.glance_attention.config import StudyConfig
from src.glance_attention.schemas import Aoi, Box, CenterBias, JitterRow, StabilityRow
from src.glance_attention.stats import Density, aoi_shares, exclusive_masks

type Shifts = dict[str, list[tuple[float, float, float, float]]]
# shares[variant][prior] -> one {aoi: share %} per draw.
type DrawShares = dict[str, dict[CenterBias, list[dict[str, float]]]]


def draw_shifts(aois: dict[str, Aoi], jitter_pct: float, rng: np.random.Generator) -> Shifts:
    """Return, per AOI and box, four edge shifts as fractions of the box size, uniform in +-`jitter_pct` %."""
    limit = jitter_pct / 100
    return {name: [tuple(rng.uniform(-limit, limit, 4)) for _ in aoi.boxes] for name, aoi in aois.items()}


def shift_box(box: Box, shifts: tuple[float, float, float, float], width: int, height: int) -> Box:
    """Move each edge of `box` by its shift, clip to the image and keep at least one pixel."""
    x0, y0, x1, y1 = box
    box_w, box_h = x1 - x0, y1 - y0
    new_x0 = min(max(0, round(x0 + shifts[0] * box_w)), width - 1)
    new_y0 = min(max(0, round(y0 + shifts[1] * box_h)), height - 1)
    new_x1 = min(max(new_x0 + 1, round(x1 + shifts[2] * box_w)), width)
    new_y1 = min(max(new_y0 + 1, round(y1 + shifts[3] * box_h)), height)
    return (new_x0, new_y0, new_x1, new_y1)


def jittered(aois: dict[str, Aoi], shifts: Shifts, width: int, height: int) -> dict[str, Aoi]:
    """Return the AOIs with every box moved by the shifts drawn for its AOI name and box position."""
    return {
        name: Aoi(
            type=aoi.type, boxes=[shift_box(box, shifts[name][i], width, height) for i, box in enumerate(aoi.boxes)]
        )
        for name, aoi in aois.items()
    }


def jitter_shares(
    aois_by_variant: dict[str, dict[str, Aoi]],
    densities: dict[str, dict[CenterBias, Density]],
    config: StudyConfig,
) -> DrawShares:
    """Return the AOI shares of every variant and prior for each seeded draw.

    One draw shifts an AOI the same way in every variant, as if one person redrew the boxes once.
    """
    rng = np.random.default_rng(config.jitter_seed)
    reference = next(iter(aois_by_variant.values()))
    shares: DrawShares = {name: {prior: [] for prior in priors} for name, priors in densities.items()}
    for _ in range(config.jitter_draws):
        shifts = draw_shifts(reference, config.jitter_pct, rng)
        for variant, aois in aois_by_variant.items():
            height, width = next(iter(densities[variant].values())).shape
            masks = exclusive_masks(jittered(aois, shifts, width, height), config.aoi_priority, height, width)
            for prior, density in densities[variant].items():
                shares[variant][prior].append(aoi_shares(masks, density))
    return shares


def jitter_rows(shares: DrawShares, base_shares: dict[tuple[str, CenterBias], dict[str, float]]) -> list[JitterRow]:
    """Return mean, SD, min and max of each AOI's share over the draws, next to its unjittered share."""
    rows = []
    for variant, by_prior in shares.items():
        for prior, draws in by_prior.items():
            for aoi, base in base_shares[(variant, prior)].items():
                values = np.array([draw[aoi] for draw in draws])
                rows.append(
                    JitterRow(
                        variant=variant,
                        centerbias=prior,
                        aoi=aoi,
                        share_pct=base,
                        jitter_mean=float(values.mean()),
                        jitter_sd=float(values.std()),
                        jitter_min=float(values.min()),
                        jitter_max=float(values.max()),
                        draws=len(draws),
                    )
                )
    return rows


def _price_order(shares: dict[str, dict[str, float]], aoi: str) -> list[str]:
    """Return the variants ordered by their share on `aoi`, highest first."""
    return sorted(shares, key=lambda variant: -shares[variant][aoi])


def stability_rows(
    shares: DrawShares,
    base_shares: dict[tuple[str, CenterBias], dict[str, float]],
    baseline: str,
    config: StudyConfig,
) -> list[StabilityRow]:
    """Return how often the price-share ordering and each product-drop flag match the unjittered result."""
    price, product, threshold = config.moving_aoi, config.product_aoi, config.product_drop_threshold_pct
    rows = []
    for prior in next(iter(shares.values())):
        base = {variant: base_shares[(variant, prior)] for variant in shares}
        draws = [{variant: shares[variant][prior][i] for variant in shares} for i in range(config.jitter_draws)]
        same_order = [_price_order(draw, price) == _price_order(base, price) for draw in draws]
        rows.append(_stability(prior, "price_share_order", same_order))
        for variant in (name for name in shares if name != baseline):
            base_held = is_product_held(base[baseline][product], base[variant][product], threshold)
            same_flag = [
                is_product_held(draw[baseline][product], draw[variant][product], threshold) == base_held
                for draw in draws
            ]
            rows.append(_stability(prior, f"product_drop_flag:{variant}", same_flag))
    return rows


def _stability(prior: CenterBias, check: str, same: list[bool]) -> StabilityRow:
    """Return one stability row from per-draw `same as unjittered` answers."""
    return StabilityRow(centerbias=prior, check=check, unchanged_pct=100 * sum(same) / len(same), draws=len(same))
