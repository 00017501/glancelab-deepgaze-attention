"""Command line: validate a study, run DeepGaze IIE on its variants, compare them to the baseline, report."""

import argparse
import logging
import os
from pathlib import Path

from src.glance_attention import CAVEAT, PLACEHOLDER_BANNER
from src.glance_attention.pipeline import compare_study, report_study, run_study
from src.glance_attention.placeholder import make_placeholders
from src.glance_attention.preview import preview_study
from src.glance_attention.study import Study, load_study
from src.glance_attention.validate import check_study, write_lock

logger = logging.getLogger(__name__)

EPILOG = "Workflow: preview -> validate -> run -> compare -> report. Details: README.md and docs/METHOD.md."
# Current Opus model ID; the audit record also stores the model that actually answered.
DEFAULT_AOI_MODEL = "claude-opus-5-5"
# Box placement is careful visual work, so ask for more than the default effort.
DEFAULT_AOI_EFFORT = "high"


def build_parser() -> argparse.ArgumentParser:
    """Return the parser with one subcommand per pipeline step and helper."""
    parser = argparse.ArgumentParser(prog="python -m src.glance_attention", description=__doc__, epilog=EPILOG)
    commands = parser.add_subparsers(dest="command", required=True)

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--study", type=Path, default=Path("data"), help="study folder (default: data)")
        return command

    add("validate", "check images and AOI files, then lock the AOIs")
    run = add("run", "run the model on every variant; needs locked AOIs")
    run.add_argument("--skip-model", action="store_true", help="reuse the saved densities instead of the model")
    add("compare", "deltas against the baseline and the price/product key test")
    add("report", "write report.md and the cross-tool long table")
    add("preview", "draw the AOI boxes on the images and list them in pixels and %")
    placeholder = add("placeholder", "generate placeholder images and AOI files into a placeholder study")
    placeholder.add_argument("--size", default="1080x1350", help="image size as WIDTHxHEIGHT")
    placeholder.add_argument("--variants", type=int, default=3, help="number of variants (A, B, C, ...)")
    aoi = add("aoi", "AI-proposed AOI boxes: `propose` asks Claude, `apply` adopts a reviewed proposal")
    aoi.add_argument("action", choices=["propose", "apply"])
    aoi.add_argument("variant", help="variant name (the image file name without extension)")
    aoi.add_argument("--prompt", type=Path, default=Path("prompts/aoi/annotation.txt"))
    aoi.add_argument("--model", default=DEFAULT_AOI_MODEL)
    aoi.add_argument("--effort", default=DEFAULT_AOI_EFFORT, choices=["low", "medium", "high", "xhigh", "max"])
    aoi.add_argument("--staging", type=Path, default=Path("provenance/aois"), help="folder for proposals and records")
    return parser


def _validate(study: Study) -> None:
    """Report every finding, then lock the AOIs or exit when there are errors."""
    findings = check_study(study)
    for warning in findings.warnings:
        logger.warning("validate_warning %s", warning)
    for error in findings.errors:
        logger.error("validate_error %s", error)
    if findings.errors:
        raise SystemExit(f"validation failed with {len(findings.errors)} error(s); AOIs not locked")
    lock = write_lock(study)
    logger.info("aois_locked variants=%d locked_utc=%s file=%s", len(lock.files), lock.locked_utc, study.lock_path)


def _placeholder(study: Study, args: argparse.Namespace) -> None:
    """Parse the size and generate the placeholder variants."""
    width, _, height = args.size.partition("x")
    if not (width.isdigit() and height.isdigit()):
        raise SystemExit(f"--size must look like 1080x1350, not {args.size}")
    make_placeholders(study, (int(width), int(height)), args.variants)


def _aoi(study: Study, args: argparse.Namespace) -> None:
    """Propose AOI boxes for one variant with Claude, or adopt a reviewed proposal."""
    from src.glance_attention.annotate.annotate import AnnotationRequest, annotate
    from src.glance_attention.annotate.apply import apply_proposal

    variants = {variant.name: variant for variant in study.variants}
    if args.variant not in variants:
        raise SystemExit(f"no image named {args.variant} in {study.root / 'images'}; variants: {sorted(variants)}")
    variant = variants[args.variant]
    if args.action == "apply":
        apply_proposal(study, variant, args.staging / f"{study.root.name}__{variant.name}.json")
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set; export it in your own terminal first")
    key = f"{study.root.name}__{variant.name}"
    annotate(
        f"anthropic:{args.model}", AnnotationRequest(key, variant.image_path, args.prompt, args.effort), args.staging
    )


def main() -> None:
    """Parse arguments, configure logging and run the subcommand."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args()
    study = load_study(args.study)
    if study.config.placeholder:
        logger.warning(
            "placeholder_study %s: every output of this study is marked and must not be reported", PLACEHOLDER_BANNER
        )
    if args.command == "validate":
        _validate(study)
    elif args.command == "run":
        run_study(study, skip_model=args.skip_model)
    elif args.command == "compare":
        compare_study(study)
    elif args.command == "report":
        report_study(study)
    elif args.command == "preview":
        preview_study(study)
    elif args.command == "placeholder":
        _placeholder(study, args)
    else:
        _aoi(study, args)
    logger.info("caveat %s", CAVEAT)
