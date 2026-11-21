"""The Markdown report of one study."""

from dataclasses import dataclass

from src.glance_attention import CAVEAT, PLACEHOLDER_BANNER
from src.glance_attention.config import StudyConfig
from src.glance_attention.runlog import RunLog
from src.glance_attention.schemas import AoiRow, CenterBias, JitterRow, StabilityRow, SummaryRow, VerdictRow
from src.glance_attention.tables import format_cell, md_table


@dataclass(frozen=True)
class ReportData:
    """Everything the report shows, already computed."""

    config: StudyConfig
    log: RunLog
    aoi_rows: list[AoiRow]
    summaries: list[SummaryRow]
    verdicts: list[VerdictRow]
    jitter: list[JitterRow]
    stability: list[StabilityRow]


def _run_section(log: RunLog) -> list[str]:
    """Return the run facts, with a loud warning when the AOIs changed after an earlier run."""
    size = next(iter(log.images.values()))
    lines = [
        "## Run",
        "",
        f"- Run date (UTC): {log.run_utc}",
        f"- Model: {log.model}, DeepGaze commit `{log.deepgaze_commit[:7]}`, device `{log.device}`",
        f"- Pipeline: version {log.pipeline_version}, commit `{log.git_commit[:7]}`"
        + (" (uncommitted changes present)" if log.is_git_dirty else ""),
        f"- Images: {len(log.images)} variants, {size.width} x {size.height} px; baseline `{log.baseline}`",
        f"- AOIs locked (UTC): {log.aoi_lock.locked_utc}, before this model run",
        "",
    ]
    if log.has_aois_changed_since_a_run:
        lines += ["> **Warning: the AOI files changed after an earlier model run on this study.**", ""]
    return lines


def _share_table(data: ReportData, centerbias: CenterBias) -> str:
    """Return variants by AOI share %, with clarity and the first-look order."""
    rows = [row for row in data.aoi_rows if row.centerbias == centerbias]
    aois = list(dict.fromkeys(row.aoi for row in rows))
    body = []
    for summary in (summary for summary in data.summaries if summary.centerbias == centerbias):
        shares = {row.aoi: row.share_pct for row in rows if row.variant == summary.variant}
        name = summary.variant + (" (baseline)" if summary.variant == data.log.baseline else "")
        cells = [format_cell(shares.get(aoi)) for aoi in aois]
        body.append([name, *cells, format_cell(summary.clarity, 3), summary.first_look_order])
    return md_table(["Variant", *(f"{aoi} %" for aoi in aois), "Clarity (0-1)", "First-look order (by peak)"], body)


def _verdict_table(data: ReportData, centerbias: CenterBias) -> str:
    """Return the key test per variant: price share change, product share change, verdict."""
    headers = ["Variant", "Price %", "Price change (pp)", "Product %", "Product change (% of baseline)"]
    headers += ["Product density change (%)", "Verdict"]
    body = [
        [
            row.variant,
            format_cell(row.price_share_pct),
            format_cell(row.price_delta_pp, 2),
            format_cell(row.product_share_pct),
            format_cell(row.product_delta_rel_pct),
            format_cell(row.product_density_delta_rel_pct),
            row.verdict,
        ]
        for row in data.verdicts
        if row.centerbias == centerbias
    ]
    return md_table(headers, body)


def _aoi_tables(data: ReportData) -> list[str]:
    """Return one per-AOI table per variant for the primary prior."""
    lines = []
    headers = ["AOI", "Type", "% attention", "% area", "Density", "Share rank", "First-look rank"]
    for summary in (summary for summary in data.summaries if summary.centerbias == CenterBias.MIT1003):
        body = [
            [
                row.aoi,
                row.type,
                format_cell(row.share_pct),
                format_cell(row.area_pct),
                format_cell(row.density, 2),
                format_cell(row.share_rank),
                format_cell(row.first_look_rank),
            ]
            for row in data.aoi_rows
            if (row.variant, row.centerbias) == (summary.variant, CenterBias.MIT1003)
        ]
        lines += [f"### Variant {summary.variant}", "", md_table(headers, body), ""]
    return lines


def _jitter_section(data: ReportData) -> list[str]:
    """Return the jitter ranges for the price and product AOIs and the stability of the conclusions."""
    config = data.config
    watched = (config.moving_aoi, config.product_aoi)
    body = [
        [row.variant, row.centerbias, row.aoi]
        + [
            format_cell(value, 2)
            for value in (row.share_pct, row.jitter_mean, row.jitter_sd, row.jitter_min, row.jitter_max)
        ]
        for row in data.jitter
        if row.aoi in watched
    ]
    stability = [[row.centerbias, row.check, format_cell(row.unchanged_pct)] for row in data.stability]
    return [
        "## Robustness: jittered AOI boxes",
        "",
        f"Every box edge was moved at random by up to {config.jitter_pct:g}% of the box's width or height, "
        f"{config.jitter_draws} times (seed {config.jitter_seed}). Shares are % of predicted attention.",
        "",
        md_table(["Variant", "Prior", "AOI", "Share", "Jitter mean", "SD", "Min", "Max"], body),
        "",
        "How often a conclusion stays the same as with the original boxes:",
        "",
        md_table(["Prior", "Check", "Unchanged (% of draws)"], stability),
        "",
    ]


def build_markdown(data: ReportData) -> str:
    """Return `report.md`: run facts, shares, key test, sensitivity, robustness and reading notes."""
    config, primary, sensitivity = data.config, CenterBias.MIT1003, CenterBias.UNIFORM
    banner = [f"> **{PLACEHOLDER_BANNER.upper()}.** Generated from placeholder images. Never cite these numbers.", ""]
    lines = [f"# {config.title}: predicted attention (DeepGaze IIE)", ""]
    lines += banner if config.placeholder else []
    lines += [f"_{CAVEAT}_", "", *_run_section(data.log)]
    lines += ["## Attention share per AOI (primary: MIT1003 centre bias)", "", _share_table(data, primary), ""]
    lines += [
        f"## Key test against baseline {data.log.baseline}",
        "",
        "Does the price share go up while the product share holds? A variant is flagged when its product "
        f"share falls by more than {config.product_drop_threshold_pct:g}% of the baseline product share.",
        "",
        _verdict_table(data, primary),
        "",
        "## Per-variant AOI tables (primary)",
        "",
        *_aoi_tables(data),
        "## Sensitivity: no centre bias",
        "",
        "The same metrics with a uniform prior. The centre bias favours central positions, so a position "
        "that wins only in the primary table may be winning because it is central.",
        "",
        _share_table(data, sensitivity),
        "",
        _verdict_table(data, sensitivity),
        "",
        *_jitter_section(data),
        "## Reading notes",
        "",
        "- Density = attention % divided by area %; above 1 means the AOI draws more attention than its size.",
        f"- Where the '{config.moving_aoi}' box covers another AOI, those pixels count for '{config.moving_aoi}' only.",
        "- First-look order ranks AOIs by their peak predicted density. It is not a scanpath.",
        "- Clarity barely differs between variants of one ad; do not read small differences into it.",
        f"- {CAVEAT}",
        "",
    ]
    return "\n".join(lines)
