"""Adopt a reviewed proposal as a variant's AOI file, keeping the fixed AOIs identical across variants."""

import json
import logging
from pathlib import Path

from PIL import Image

from src.glance_attention.schemas import VariantAois, load_aois
from src.glance_attention.study import Study, Variant
from src.glance_attention.validate import box_problems

logger = logging.getLogger(__name__)


def apply_proposal(study: Study, variant: Variant, entry_path: Path) -> None:
    """Write `aois/<variant>.json` from the proposal; refuse an existing file and failing boxes.

    The baseline takes every AOI from its proposal. Any other variant takes only the moving AOI from
    its proposal and copies the fixed AOIs from the baseline's file, so they cannot drift apart.
    """
    if variant.aoi_path.exists():
        msg = f"{variant.aoi_path} already exists; AOI files are never replaced silently. Remove it first if intended."
        raise SystemExit(msg)
    if not entry_path.exists():
        raise SystemExit(f"no proposal at {entry_path}; run `aoi propose {variant.name}` first")
    proposal = load_aois(entry_path)
    moving, aois = study.config.moving_aoi, dict(proposal.aois)
    if moving not in aois:
        raise SystemExit(f"the proposal has no AOI named '{moving}'; edit the proposal's names first")
    if variant.name != study.baseline:
        baseline_path = variant.aoi_path.with_name(f"{study.baseline}.json")
        if not baseline_path.exists():
            raise SystemExit(f"apply the baseline {study.baseline} first; its fixed AOIs are copied to every variant")
        fixed = {name: aoi for name, aoi in load_aois(baseline_path).aois.items() if name != moving}
        aois = {moving: aois[moving], **fixed}
    width, height = Image.open(variant.image_path).size
    problems = box_problems(aois, moving, width, height)
    if problems:
        raise SystemExit(f"{entry_path} fails the checks; fix the boxes first: " + "; ".join(problems))
    spec = VariantAois(image=variant.image_path.name, aois=aois)
    variant.aoi_path.parent.mkdir(parents=True, exist_ok=True)
    variant.aoi_path.write_text(json.dumps(spec.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    logger.info("proposal_applied variant=%s file=%s aois=%s", variant.name, variant.aoi_path, list(aois))
