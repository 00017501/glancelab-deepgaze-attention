"""The long-format cross-tool table: DeepGaze rows filled in, empty rows for the tools exported by hand."""

from src.glance_attention import PIPELINE_VERSION
from src.glance_attention.config import ExternalTool
from src.glance_attention.runlog import RunLog
from src.glance_attention.schemas import IMAGE_LEVEL, AoiRow, CenterBias, CompareRow, LongRow, SummaryRow
from src.glance_attention.study import Study

TOOL_NAME = "deepgaze_iie"
# Metrics computed without the centre bias carry this suffix; the primary set carries none.
SENSITIVITY_SUFFIX = "_no_centerbias"
# Row field -> (metric name, scale) for the per-AOI and the whole-image DeepGaze metrics.
AOI_METRICS = {
    "share_pct": ("attention_pct", "0-100 % of predicted attention"),
    "area_pct": ("area_pct", "0-100 % of image area"),
    "density": ("attention_density", "attention % per area %; 1 = proportional to size"),
    "share_rank": ("aoi_rank", "1 = AOI with the highest attention %"),
    "first_look_rank": ("first_look_rank", "1 = AOI with the highest peak density (not a scanpath)"),
}
IMAGE_METRICS = {
    "clarity": ("clarity", "0-1; higher = more focused (1 - normalised entropy)"),
    "entropy_norm": ("entropy_norm", "0-1; lower = more focused"),
    "top10_pct": ("top10_pct", "0-100 % of attention in the top 10 % of pixels"),
}
DELTA_METRIC = ("attention_pct_delta_vs_baseline", "percentage points vs the baseline variant")


def _suffix(centerbias: CenterBias) -> str:
    """Return the metric-name suffix for a prior."""
    return "" if centerbias == CenterBias.MIT1003 else SENSITIVITY_SUFFIX


def version_label(log: RunLog) -> str:
    """Return the `version` cell: model commit and pipeline version, marked when the study is a placeholder."""
    label = f"deepgaze@{log.deepgaze_commit[:7]} pipeline@{PIPELINE_VERSION}"
    return f"PLACEHOLDER {label}" if log.is_placeholder else label


def deepgaze_rows(
    aoi_rows: list[AoiRow], summaries: list[SummaryRow], comparison: list[CompareRow], log: RunLog
) -> list[LongRow]:
    """Return every DeepGaze metric as long rows: per AOI, per image, and the share change vs baseline."""
    stamp = {"tool": TOOL_NAME, "run_date": log.run_date, "version": version_label(log)}
    rows = []
    for row in aoi_rows:
        for field, (metric, scale) in AOI_METRICS.items():
            # The rest of the image has no rank, so it gets no rank rows.
            if getattr(row, field) is None:
                continue
            name = metric + _suffix(row.centerbias)
            rows.append(
                LongRow(variant=row.variant, aoi=row.aoi, metric=name, value=getattr(row, field), scale=scale, **stamp)
            )
    for summary in summaries:
        for field, (metric, scale) in IMAGE_METRICS.items():
            name = metric + _suffix(summary.centerbias)
            rows.append(
                LongRow(
                    variant=summary.variant,
                    aoi=IMAGE_LEVEL,
                    metric=name,
                    value=getattr(summary, field),
                    scale=scale,
                    **stamp,
                )
            )
    for change in comparison:
        if change.metric == "share_pct" and change.aoi != IMAGE_LEVEL:
            name = DELTA_METRIC[0] + _suffix(change.centerbias)
            rows.append(
                LongRow(
                    variant=change.variant,
                    aoi=change.aoi,
                    metric=name,
                    value=change.delta,
                    scale=DELTA_METRIC[1],
                    **stamp,
                )
            )
    return rows


def template_rows(study: Study, aoi_names: list[str], tools: list[ExternalTool]) -> list[LongRow]:
    """Return one empty-value row per tool, variant, metric and (for AOI metrics) AOI, to be filled by hand."""
    version = "PLACEHOLDER" if study.config.placeholder else ""
    rows = []
    for tool in tools:
        for variant in study.variants:
            for metric in tool.metrics:
                for aoi in aoi_names if metric.level == "aoi" else [IMAGE_LEVEL]:
                    rows.append(
                        LongRow(
                            tool=tool.name,
                            variant=variant.name,
                            aoi=aoi,
                            metric=metric.metric,
                            value=None,
                            scale=metric.scale,
                            run_date="",
                            version=version,
                        )
                    )
    return rows
