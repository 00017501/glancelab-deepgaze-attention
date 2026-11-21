"""A study folder: its config, the variants found in `images/`, and where its outputs go."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.glance_attention.config import StudyConfig, load_config
from src.glance_attention.schemas import CenterBias

# Image files picked up from `images/`; anything else in the folder is ignored.
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
# Prefix on every output file of a placeholder study, so none can be mistaken for a result.
PLACEHOLDER_PREFIX = "PLACEHOLDER_"


@dataclass(frozen=True)
class Variant:
    """One version of the ad: its name (the image file stem), its image and its AOI file."""

    name: str
    image_path: Path
    aoi_path: Path


@dataclass(frozen=True)
class Study:
    """A study folder with its config and its variants in name order."""

    root: Path
    config: StudyConfig
    variants: list[Variant]

    @property
    def baseline(self) -> str:
        """Return the baseline variant name: the configured one, else the first by name."""
        if self.config.baseline is not None:
            return self.config.baseline
        return self.variants[0].name if self.variants else ""

    @property
    def lock_path(self) -> Path:
        """Return the file that records the AOI hashes fixed by `validate`."""
        return self.root / "aoi_lock.json"

    def output(self, *parts: str) -> Path:
        """Return a path under `output/`; the file name gets the placeholder prefix when the study is one."""
        prefix = PLACEHOLDER_PREFIX if self.config.placeholder else ""
        return self.root.joinpath("output", *parts[:-1], prefix + parts[-1])

    def density_path(self, variant: str, centerbias: CenterBias) -> Path:
        """Return where the saved density of one variant under one prior lives."""
        return self.output("density", f"{variant}__{centerbias}.npy")


def load_study(root: Path) -> Study:
    """Read the config and list one variant per image file in `images/`, sorted by name."""
    if not root.is_dir():
        msg = f"study folder {root} does not exist"
        raise SystemExit(msg)
    images = sorted(path for path in (root / "images").glob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
    variants = [Variant(path.stem, path, root / "aois" / f"{path.stem}.json") for path in images]
    return Study(root, load_config(root), variants)


def sha256_of(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()
