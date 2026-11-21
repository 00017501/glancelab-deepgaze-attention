"""The `run`, `compare` and `report` steps of one study."""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from src.glance_attention.compare import compare_to_baseline, verdicts
from src.glance_attention.jitter import jitter_rows, jitter_shares, stability_rows
from src.glance_attention.longtable import deepgaze_rows, template_rows
from src.glance_attention.report import ReportData, build_markdown
from src.glance_attention.runlog import RunLog, aoi_set_sha256, read_run_log, save_run_log, start_run_log
from src.glance_attention.schemas import (
    REST_AOI_NAME,
    Aoi,
    AoiRow,
    CenterBias,
    CompareRow,
    JitterRow,
    LongRow,
    StabilityRow,
    SummaryRow,
    VerdictRow,
    load_aois,
)
from src.glance_attention.stats import Density, compute_rows
from src.glance_attention.study import Study, sha256_of
from src.glance_attention.tables import read_csv, write_csv
from src.glance_attention.validate import check_study, lock_problem, read_lock
from src.glance_attention.visuals import aoi_overlay, heat_overlay, panel, stamp

logger = logging.getLogger(__name__)

type Densities = dict[str, dict[CenterBias, Density]]


@dataclass(frozen=True)
class Results:
    """The AOIs and statistics of every variant under both priors."""

    aois: dict[str, dict[str, Aoi]]
    aoi_rows: list[AoiRow]
    summaries: list[SummaryRow]


def _stop_unless_ready(study: Study) -> None:
    """Exit with the reason when the study fails validation or its AOIs are not locked."""
    findings = check_study(study)
    problem = "; ".join(findings.errors) or lock_problem(study)
    if problem:
        raise SystemExit(f"cannot continue: {problem}")


def _load_densities(study: Study) -> Densities:
    """Return the saved densities of every variant; exit when `run` has not produced them yet."""
    densities: Densities = {}
    for variant in study.variants:
        paths = {prior: study.density_path(variant.name, prior) for prior in CenterBias}
        missing = [path.name for path in paths.values() if not path.exists()]
        if missing:
            raise SystemExit(f"no saved density {missing} for variant {variant.name}; run `run` first")
        densities[variant.name] = {prior: np.load(path) for prior, path in paths.items()}
    return densities


def _predict_densities(study: Study, centerbias_path: Path) -> Densities:
    """Run the model on every variant under both priors and save each density."""
    from src.glance_attention.model import DeepGazeRunner

    runner, densities = DeepGazeRunner(), {}
    for variant in study.variants:
        densities[variant.name] = {}
        for prior in CenterBias:
            logger.info("variant_started variant=%s centerbias=%s", variant.name, prior)
            path = centerbias_path if prior == CenterBias.MIT1003 else None
            density = runner.predict_density(variant.image_path, path)
            study.density_path(variant.name, prior).parent.mkdir(parents=True, exist_ok=True)
            np.save(study.density_path(variant.name, prior), density)
            densities[variant.name][prior] = density
    return densities


def compute_results(study: Study, densities: Densities) -> Results:
    """Return the statistics of every variant under both priors, in variant order."""
    aois = {variant.name: load_aois(variant.aoi_path).aois for variant in study.variants}
    aoi_rows, summaries = [], []
    for name, by_prior in densities.items():
        for prior, density in by_prior.items():
            rows, summary = compute_rows((name, prior), aois[name], study.config.aoi_priority, density)
            aoi_rows += rows
            summaries.append(summary)
    return Results(aois, aoi_rows, summaries)


def _write_images(study: Study, densities: Densities, results: Results) -> None:
    """Save each variant's heatmap and AOI overlay (primary prior) and one panel per prior, on shared scales."""
    is_placeholder = study.config.placeholder
    shares = {(row.variant, row.centerbias, row.aoi): row.share_pct for row in results.aoi_rows}
    for prior in CenterBias:
        scale_max = max(by_prior[prior].max() for by_prior in densities.values())
        tiles = []
        for variant in study.variants:
            image = Image.open(variant.image_path).convert("RGB")
            heat = heat_overlay(image, densities[variant.name][prior], scale_max)
            aois = results.aois[variant.name]
            overlay = aoi_overlay(
                heat, aois, {name: f"{name} {shares[(variant.name, prior, name)]:.1f}%" for name in aois}
            )
            tiles.append((variant.name + (" (baseline)" if variant.name == study.baseline else ""), overlay))
            if prior == CenterBias.MIT1003:
                study.output("heatmaps", "x").parent.mkdir(parents=True, exist_ok=True)
                stamp(heat, is_placeholder=is_placeholder).save(study.output("heatmaps", f"{variant.name}_heatmap.png"))
                stamp(overlay, is_placeholder=is_placeholder).save(study.output("heatmaps", f"{variant.name}_aoi.png"))
        suffix = "" if prior == CenterBias.MIT1003 else "_no_centerbias"
        title = f"{study.config.title} | prior: {prior} | one colour scale for all variants"
        panel(tiles, is_placeholder=is_placeholder, title=title).save(study.output(f"panel{suffix}.png"))


def _write_jitter(study: Study, densities: Densities, results: Results) -> None:
    """Run the jitter check and save its two tables."""
    base = {}
    for row in results.aoi_rows:
        base.setdefault((row.variant, row.centerbias), {})[row.aoi] = row.share_pct
    shares = jitter_shares(results.aois, densities, study.config)
    write_csv(study.output("jitter.csv"), jitter_rows(shares, base), JitterRow)
    stability = stability_rows(shares, base, study.baseline, study.config)
    write_csv(study.output("jitter_stability.csv"), stability, StabilityRow)


def _check_reusable(study: Study, log: RunLog | None) -> None:
    """Exit unless the saved densities were made from the current images and the current AOI set."""
    lock = read_lock(study.lock_path)
    if log is None or lock is None:
        raise SystemExit("--skip-model needs an earlier full `run` on this study")
    images_match = all(
        sha256_of(v.image_path) == log.images[v.name].sha256 for v in study.variants if v.name in log.images
    )
    if len(log.images) != len(study.variants) or not images_match or aoi_set_sha256(lock) != log.aoi_set_sha256:
        raise SystemExit("images or AOIs changed since the last model run; do a full `run` so the log records it")


def run_study(study: Study, *, skip_model: bool) -> None:
    """Run the model on every variant and write densities, tables and images.

    1. Stop unless the study validates and its AOI files match the lock.
    2. Write the run log, with the AOI hashes and lock time, before the model loads.
    3. Predict the density of every variant under both priors (or reuse the saved ones).
    4. Compute the statistics and write the per-variant tables and the summary.
    5. Draw heatmaps, AOI overlays and panels, and run the jitter check.
    6. Mark the run log finished.
    """
    # 1. Validation and lock.
    _stop_unless_ready(study)
    lock = read_lock(study.lock_path)
    centerbias_path = Path(study.config.centerbias_path)
    if not skip_model and not centerbias_path.exists():
        raise SystemExit(f"centre-bias file {centerbias_path} not found; run setup.sh")

    # 2. Run log first, so the AOI state is on record before any heatmap exists.
    if skip_model:
        _check_reusable(study, read_run_log(study))
        log = None
    else:
        log = start_run_log(study, lock, centerbias_path)
        if log.has_aois_changed_since_a_run:
            logger.warning("aois_changed_after_a_previous_run recorded_in=run_log.json")

    # 3. Densities.
    densities = _load_densities(study) if skip_model else _predict_densities(study, centerbias_path)

    # 4. Statistics and tables.
    results = compute_results(study, densities)
    for variant in study.variants:
        rows = [row for row in results.aoi_rows if row.variant == variant.name]
        write_csv(study.output(f"{variant.name}_aoi.csv"), rows, AoiRow)
    write_csv(study.output("summary.csv"), results.summaries, SummaryRow)

    # 5. Images and robustness.
    _write_images(study, densities, results)
    _write_jitter(study, densities, results)

    # 6. Done.
    if log is not None:
        save_run_log(study, log.model_copy(update={"status": "finished"}))
    logger.info("run_finished study=%s variants=%d", study.root, len(study.variants))


def compare_study(study: Study) -> tuple[list[CompareRow], list[VerdictRow]]:
    """Write `compare.csv` and `verdict.csv` from the saved densities; return their rows."""
    _stop_unless_ready(study)
    results = compute_results(study, _load_densities(study))
    comparison = compare_to_baseline(results.aoi_rows, results.summaries, study.baseline)
    verdict_rows = verdicts(results.aoi_rows, study.baseline, study.config)
    write_csv(study.output("compare.csv"), comparison, CompareRow)
    write_csv(study.output("verdict.csv"), verdict_rows, VerdictRow)
    for row in verdict_rows:
        logger.info("verdict variant=%s centerbias=%s verdict=%s", row.variant, row.centerbias, row.verdict)
    return comparison, verdict_rows


def report_study(study: Study) -> None:
    """Write `report.md` and the cross-tool long table from the saved densities, tables and run log."""
    _stop_unless_ready(study)
    log = read_run_log(study)
    if log is None or log.status != "finished":
        raise SystemExit("no finished run log; run `run` first")
    results = compute_results(study, _load_densities(study))
    comparison = compare_to_baseline(results.aoi_rows, results.summaries, study.baseline)
    data = ReportData(
        config=study.config,
        log=log,
        aoi_rows=results.aoi_rows,
        summaries=results.summaries,
        verdicts=verdicts(results.aoi_rows, study.baseline, study.config),
        jitter=read_csv(study.output("jitter.csv"), JitterRow),
        stability=read_csv(study.output("jitter_stability.csv"), StabilityRow),
    )
    study.output("report.md").write_text(build_markdown(data), encoding="utf-8")
    aoi_names = [*results.aois[study.baseline], REST_AOI_NAME]
    long_rows = deepgaze_rows(results.aoi_rows, results.summaries, comparison, log)
    long_rows += template_rows(study, aoi_names, study.config.external_tools)
    write_csv(study.output("cross_tool_long.csv"), long_rows, LongRow)
    logger.info("report_written study=%s rows=%d", study.root, len(long_rows))
