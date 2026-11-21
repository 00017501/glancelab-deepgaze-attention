"""Tests for the AOI statistics, the comparison against the baseline and the jitter check."""

import numpy as np
import pytest

from src.glance_attention.compare import compare_to_baseline, is_product_held, verdicts
from src.glance_attention.config import StudyConfig
from src.glance_attention.jitter import jitter_rows, jitter_shares, shift_box, stability_rows
from src.glance_attention.schemas import REST_AOI_NAME, Aoi, CenterBias
from src.glance_attention.stats import compute_rows, entropy_norm, exclusive_masks, top_k_share

PRIOR = CenterBias.MIT1003


def _aois(price_box: list[int]) -> dict[str, Aoi]:
    raw = {"price": price_box, "product": [10, 10, 30, 30], "logo": [0, 0, 5, 5]}
    return {name: Aoi.model_validate({"type": name, "boxes": [box]}) for name, box in raw.items()}


def _density(hot_box: list[int]) -> np.ndarray:
    density = np.ones((40, 40))
    x0, y0, x1, y1 = hot_box
    density[y0:y1, x0:x1] = 50
    return density / density.sum()


def test_price_wins_overlapping_pixels_and_every_pixel_has_one_owner() -> None:
    masks = exclusive_masks(_aois([25, 25, 35, 35]), ["price"], 40, 40)
    assert list(masks) == ["price", "product", "logo", REST_AOI_NAME]
    assert masks["price"].sum() == 100
    assert masks["product"].sum() == 400 - 25
    assert np.array_equal(sum(mask.astype(int) for mask in masks.values()), np.ones((40, 40), int))


def test_shares_sum_to_100_and_density_is_share_per_area() -> None:
    rows, summary = compute_rows(("A", PRIOR), _aois([25, 25, 35, 35]), ["price"], _density([25, 25, 35, 35]))
    assert sum(row.share_pct for row in rows) == pytest.approx(100)
    assert sum(row.area_pct for row in rows) == pytest.approx(100)
    price = rows[0]
    assert price.density == pytest.approx(price.share_pct / price.area_pct)
    assert (price.share_rank, price.first_look_rank) == (1, 1)
    assert rows[-1].aoi == REST_AOI_NAME
    assert rows[-1].share_rank is None
    assert summary.first_look_order.startswith("price > ")
    assert summary.clarity == pytest.approx(1 - summary.entropy_norm)


def test_entropy_is_one_for_uniform_and_top_share_matches_the_fraction() -> None:
    uniform = np.full((40, 40), 1 / 1600)
    assert entropy_norm(uniform) == pytest.approx(1.0)
    assert top_k_share(uniform) == pytest.approx(0.10)


def _two_variants() -> tuple[list, list]:
    aoi_rows, summaries = [], []
    for variant, price_box in (("A", [32, 32, 38, 38]), ("B", [12, 12, 18, 18])):
        rows, summary = compute_rows((variant, PRIOR), _aois(price_box), ["price"], _density(price_box))
        aoi_rows += rows
        summaries.append(summary)
    return aoi_rows, summaries


def test_compare_gives_deltas_against_the_baseline_for_every_aoi() -> None:
    aoi_rows, summaries = _two_variants()
    rows = compare_to_baseline(aoi_rows, summaries, "A")
    assert {row.variant for row in rows} == {"B"}
    assert {row.aoi for row in rows} == {"price", "product", "logo", REST_AOI_NAME, "(image)"}
    product = next(row for row in rows if (row.aoi, row.metric) == ("product", "share_pct"))
    assert product.delta == pytest.approx(product.variant_value - product.baseline_value)
    assert product.delta_rel_pct == pytest.approx(100 * product.delta / product.baseline_value)


def test_product_drop_flag_uses_the_relative_threshold() -> None:
    assert is_product_held(40, 36, 10)
    assert not is_product_held(40, 35.9, 10)
    aoi_rows, _ = _two_variants()
    (strict,) = verdicts(aoi_rows, "A", StudyConfig(product_drop_threshold_pct=5))
    (loose,) = verdicts(aoi_rows, "A", StudyConfig(product_drop_threshold_pct=99))
    assert strict.product_delta_rel_pct < -5
    assert not strict.is_product_held
    assert "PRODUCT DROP FLAGGED" in strict.verdict
    assert loose.is_product_held


def test_shifted_boxes_stay_inside_the_image_and_keep_a_pixel() -> None:
    assert shift_box((0, 0, 10, 10), (-0.5, -0.5, 0.5, 0.5), 12, 12) == (0, 0, 12, 12)
    x0, y0, x1, y1 = shift_box((5, 5, 6, 6), (0.9, 0.9, -0.9, -0.9), 12, 12)
    assert x1 > x0
    assert y1 > y0


def test_jitter_is_seeded_and_zero_jitter_changes_nothing() -> None:
    aois = {"A": _aois([32, 32, 38, 38]), "B": _aois([12, 12, 18, 18])}
    densities = {name: {PRIOR: _density(list(boxes["price"].boxes[0]))} for name, boxes in aois.items()}
    base = {}
    for name, variant_aois in aois.items():
        rows, _ = compute_rows((name, PRIOR), variant_aois, ["price"], densities[name][PRIOR])
        base[(name, PRIOR)] = {row.aoi: row.share_pct for row in rows}
    config = StudyConfig(jitter_draws=10)
    assert jitter_shares(aois, densities, config) == jitter_shares(aois, densities, config)
    still = StudyConfig(jitter_draws=10, jitter_pct=0)
    shares = jitter_shares(aois, densities, still)
    assert all(row.jitter_sd == pytest.approx(0) for row in jitter_rows(shares, base))
    assert all(row.unchanged_pct == 100 for row in stability_rows(shares, base, "A", still))
    moved = jitter_rows(jitter_shares(aois, densities, config), base)
    assert any(row.jitter_sd > 0 for row in moved)
