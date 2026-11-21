"""Predicted attention (DeepGaze IIE) for variants of one static ad that differ in one moved element."""

# Written into the run log and the `version` column of the cross-tool table.
PIPELINE_VERSION = "0.1.0"
# Stated on every output: these numbers are model predictions, never measurements.
CAVEAT = "Predicted free-viewing attention from DeepGaze IIE (Linardos et al., 2021). Not real eye-tracking."
# Stamped on every output of a study whose config says `placeholder = true`.
PLACEHOLDER_BANNER = "PLACEHOLDER – not results"  # noqa: RUF001
