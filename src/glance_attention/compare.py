"""Deltas of every variant against the baseline, and the key test: price up while the product holds."""

from src.glance_attention.config import StudyConfig
from src.glance_attention.schemas import IMAGE_LEVEL, AoiRow, CenterBias, CompareRow, SummaryRow, VerdictRow

# Per-AOI and whole-image metrics compared against the baseline, in table order.
AOI_METRICS = ("share_pct", "area_pct", "density", "peak", "share_rank", "first_look_rank")
IMAGE_METRICS = ("entropy_norm", "clarity", "top10_pct")


def _delta(baseline_value: float | None, variant_value: float | None) -> tuple[float | None, float | None]:
    """Return the absolute change and the change as a % of the baseline; `None` where undefined."""
    if baseline_value is None or variant_value is None:
        return None, None
    delta = variant_value - baseline_value
    return delta, (100 * delta / baseline_value if baseline_value else None)


def _metric_rows(
    labels: tuple[str, str, CenterBias, str], baseline_row: object, variant_row: object, metrics: tuple[str, ...]
) -> list[CompareRow]:
    """Return one comparison row per metric; `labels` is `(variant, baseline, prior, aoi)`."""
    variant, baseline, centerbias, aoi = labels
    rows = []
    for metric in metrics:
        baseline_value = getattr(baseline_row, metric, None)
        variant_value = getattr(variant_row, metric, None)
        delta, delta_rel_pct = _delta(baseline_value, variant_value)
        rows.append(
            CompareRow(
                variant=variant,
                baseline=baseline,
                centerbias=centerbias,
                aoi=aoi,
                metric=metric,
                baseline_value=baseline_value,
                variant_value=variant_value,
                delta=delta,
                delta_rel_pct=delta_rel_pct,
            )
        )
    return rows


def compare_to_baseline(aoi_rows: list[AoiRow], summaries: list[SummaryRow], baseline: str) -> list[CompareRow]:
    """Return every AOI and whole-image metric of each non-baseline variant against the baseline."""
    by_key = {(row.variant, row.centerbias, row.aoi): row for row in aoi_rows}
    summary_by_key = {(row.variant, row.centerbias): row for row in summaries}
    rows = []
    for summary in summaries:
        if summary.variant == baseline:
            continue
        variant, centerbias = summary.variant, summary.centerbias
        for row in (row for row in aoi_rows if (row.variant, row.centerbias) == (variant, centerbias)):
            labels = (variant, baseline, centerbias, row.aoi)
            rows += _metric_rows(labels, by_key.get((baseline, centerbias, row.aoi)), row, AOI_METRICS)
        labels = (variant, baseline, centerbias, IMAGE_LEVEL)
        rows += _metric_rows(labels, summary_by_key[(baseline, centerbias)], summary, IMAGE_METRICS)
    return rows


def is_product_held(baseline_share: float, variant_share: float, threshold_pct: float) -> bool:
    """Return whether the product share fell by no more than `threshold_pct` % of the baseline share."""
    return variant_share >= baseline_share * (1 - threshold_pct / 100)


def verdict_text(is_price_up: bool, is_held: bool) -> str:
    """Return the key-test outcome in words."""
    price = "price share up" if is_price_up else "price share not up"
    product = "product held" if is_held else "PRODUCT DROP FLAGGED"
    return f"{price}; {product}"


def verdicts(aoi_rows: list[AoiRow], baseline: str, config: StudyConfig) -> list[VerdictRow]:
    """Return the key test per non-baseline variant and prior: is the price share up and the product held?"""
    by_key = {(row.variant, row.centerbias, row.aoi): row for row in aoi_rows}
    rows = []
    for (variant, centerbias, aoi), price in by_key.items():
        if aoi != config.moving_aoi or variant == baseline:
            continue
        base_price, base_product = (by_key[(baseline, centerbias, name)] for name in (aoi, config.product_aoi))
        product = by_key[(variant, centerbias, config.product_aoi)]
        price_delta = price.share_pct - base_price.share_pct
        is_held = is_product_held(base_product.share_pct, product.share_pct, config.product_drop_threshold_pct)
        rows.append(
            VerdictRow(
                variant=variant,
                baseline=baseline,
                centerbias=centerbias,
                price_share_pct=price.share_pct,
                price_delta_pp=price_delta,
                is_price_up=price_delta > 0,
                product_share_pct=product.share_pct,
                product_delta_rel_pct=_delta(base_product.share_pct, product.share_pct)[1] or 0.0,
                product_density_delta_rel_pct=_delta(base_product.density, product.density)[1] or 0.0,
                threshold_pct=config.product_drop_threshold_pct,
                is_product_held=is_held,
                verdict=verdict_text(price_delta > 0, is_held),
            )
        )
    return rows
