"""Checks run before the model: image sizes, AOI files, fixed-versus-moving AOIs, and the AOI lock."""

import json
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

from PIL import Image
from pydantic import BaseModel, ValidationError

from src.glance_attention.schemas import Aoi, Box, VariantAois, load_aois
from src.glance_attention.stats import aoi_mask
from src.glance_attention.study import Study, sha256_of

# A comparison needs the baseline and at least one other variant.
MIN_VARIANTS = 2


class LockedFile(BaseModel):
    """The state of one AOI file when it was locked."""

    file: str
    sha256: str
    modified_utc: str


class AoiLock(BaseModel):
    """`aoi_lock.json`: proof of which AOI files were fixed, and when, before any model run."""

    locked_utc: str
    files: dict[str, LockedFile]


class Findings(BaseModel):
    """What `validate` found: errors stop the pipeline, warnings are for a human to read."""

    errors: list[str] = []
    warnings: list[str] = []


def box_problems(aois: dict[str, Aoi], moving_aoi: str, width: int, height: int) -> list[str]:
    """Return empty, inverted and out-of-image boxes, and overlaps between AOIs other than the moving one."""
    problems = []
    for name, aoi in aois.items():
        for x0, y0, x1, y1 in aoi.boxes:
            if x0 >= x1 or y0 >= y1:
                problems.append(f"{name}: box {[x0, y0, x1, y1]} has zero or negative size")
            if min(x0, y0) < 0 or x1 > width or y1 > height:
                problems.append(f"{name}: box {[x0, y0, x1, y1]} extends past the {width}x{height} image")
    masks = {name: aoi_mask(aoi.boxes, height, width) for name, aoi in aois.items() if name != moving_aoi}
    for (first, first_mask), (second, second_mask) in combinations(masks.items(), 2):
        overlap = int((first_mask & second_mask).sum())
        if overlap:
            problems.append(f"{first} and {second} overlap by {overlap} px; fixed AOIs must not overlap")
    return problems


def _box_sizes(boxes: list[Box]) -> list[tuple[int, int]]:
    """Return the `(width, height)` of each box."""
    return [(x1 - x0, y1 - y0) for x0, y0, x1, y1 in boxes]


def _check_images(study: Study, findings: Findings) -> tuple[int, int] | None:
    """Record size mismatches and return the common `(width, height)`, or `None` when sizes differ."""
    sizes = {variant.name: Image.open(variant.image_path).size for variant in study.variants}
    if len(set(sizes.values())) > 1:
        listed = ", ".join(f"{name}={width}x{height}" for name, (width, height) in sizes.items())
        findings.errors.append(f"images are not all the same size: {listed}")
        return None
    return next(iter(sizes.values()), None)


def _load_all_aois(study: Study, findings: Findings) -> dict[str, VariantAois]:
    """Load every variant's AOI file, recording missing, unreadable and orphaned files."""
    loaded = {}
    for variant in study.variants:
        if not variant.aoi_path.exists():
            findings.errors.append(f"{variant.name}: no AOI file at aois/{variant.aoi_path.name}")
            continue
        try:
            loaded[variant.name] = load_aois(variant.aoi_path)
        except (ValidationError, json.JSONDecodeError) as error:
            findings.errors.append(f"{variant.name}: aois/{variant.aoi_path.name} is not a valid AOI file: {error}")
            continue
        if loaded[variant.name].image != variant.image_path.name:
            named = loaded[variant.name].image
            findings.errors.append(f"{variant.name}: its AOI file names image '{named}', not {variant.image_path.name}")
    names = {variant.name for variant in study.variants}
    for path in sorted((study.root / "aois").glob("*.json")):
        if path.stem not in names:
            findings.errors.append(f"aois/{path.name} has no image named {path.stem} in images/")
    return loaded


def _check_against_baseline(study: Study, loaded: dict[str, VariantAois], findings: Findings) -> None:
    """Record fixed AOIs that differ from the baseline's, and a moving AOI whose box size changed."""
    moving, reference = study.config.moving_aoi, loaded[study.baseline].aois
    fixed_reference = {name: aoi for name, aoi in reference.items() if name != moving}
    for name, spec in loaded.items():
        for required in (moving, study.config.product_aoi):
            if required not in spec.aois:
                findings.errors.append(f"{name}: AOI '{required}' is missing")
        fixed = {aoi_name: aoi for aoi_name, aoi in spec.aois.items() if aoi_name != moving}
        if fixed != fixed_reference:
            findings.errors.append(
                f"{name}: fixed AOIs differ from baseline {study.baseline}; only '{moving}' may move"
            )
        if moving in spec.aois and moving in reference:
            sizes, reference_sizes = _box_sizes(spec.aois[moving].boxes), _box_sizes(reference[moving].boxes)
            if sizes != reference_sizes:
                findings.errors.append(f"{name}: '{moving}' box size {sizes} differs from baseline {reference_sizes}")


def _check_boxes(study: Study, loaded: dict[str, VariantAois], size: tuple[int, int], findings: Findings) -> None:
    """Record box problems per variant, and report where the moving AOI covers a fixed one."""
    moving, (width, height) = study.config.moving_aoi, size
    for name, spec in loaded.items():
        findings.errors += [f"{name}: {problem}" for problem in box_problems(spec.aois, moving, width, height)]
        if moving not in spec.aois:
            continue
        moving_mask = aoi_mask(spec.aois[moving].boxes, height, width)
        for aoi_name, aoi in spec.aois.items():
            overlap = int((moving_mask & aoi_mask(aoi.boxes, height, width)).sum()) if aoi_name != moving else 0
            if overlap:
                findings.warnings.append(
                    f"{name}: '{moving}' covers {overlap} px of '{aoi_name}'; those pixels count for '{moving}' only"
                )


def check_study(study: Study) -> Findings:
    """Run every pre-model check and return the errors and warnings found.

    1. The study has enough variants and a baseline that exists.
    2. All images are the same size.
    3. Every image has a valid AOI file and every AOI file has an image.
    4. Fixed AOIs are identical to the baseline's and the moving AOI keeps its box size.
    5. Boxes are inside the image, non-empty, and fixed AOIs do not overlap each other.
    """
    # 1. Variants and baseline.
    findings = Findings()
    names = [variant.name for variant in study.variants]
    if len(names) < MIN_VARIANTS:
        findings.errors.append(f"found {len(names)} image(s) in images/; a comparison needs at least {MIN_VARIANTS}")
    if names and study.baseline not in names:
        findings.errors.append(f"baseline '{study.baseline}' is not among the variants {names}")

    # 2. Image sizes.
    size = _check_images(study, findings)

    # 3. AOI files.
    loaded = _load_all_aois(study, findings)

    # 4. Fixed and moving AOIs.
    if study.baseline in loaded:
        _check_against_baseline(study, loaded, findings)

    # 5. Boxes.
    if size is not None:
        _check_boxes(study, loaded, size, findings)
    return findings


def _current_files(study: Study) -> dict[str, LockedFile]:
    """Return hash and modification time of every variant's AOI file as it is now."""
    return {
        variant.name: LockedFile(
            file=f"aois/{variant.aoi_path.name}",
            sha256=sha256_of(variant.aoi_path),
            modified_utc=datetime.fromtimestamp(variant.aoi_path.stat().st_mtime, UTC).isoformat(timespec="seconds"),
        )
        for variant in study.variants
    }


def read_lock(path: Path) -> AoiLock | None:
    """Return the stored lock, or `None` when the study has never been locked."""
    return AoiLock.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def write_lock(study: Study) -> AoiLock:
    """Lock the current AOI files; an unchanged set keeps its original lock time."""
    files, previous = _current_files(study), read_lock(study.lock_path)
    hashes = {name: locked.sha256 for name, locked in files.items()}
    if previous is not None and {name: locked.sha256 for name, locked in previous.files.items()} == hashes:
        return previous
    lock = AoiLock(locked_utc=datetime.now(UTC).isoformat(timespec="seconds"), files=files)
    study.lock_path.write_text(lock.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return lock


def lock_problem(study: Study) -> str | None:
    """Return why the AOI files cannot be trusted as locked, or `None` when they match the lock."""
    lock = read_lock(study.lock_path)
    if lock is None:
        return "the AOIs are not locked yet; run `validate` first"
    current = {name: locked.sha256 for name, locked in _current_files(study).items()}
    if current != {name: locked.sha256 for name, locked in lock.files.items()}:
        return "the AOI files changed since they were locked; run `validate` again to lock the new set"
    return None
