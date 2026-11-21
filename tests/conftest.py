"""Shared fixtures: a generated placeholder study and a model-free stand-in for a finished run."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.glance_attention.placeholder import make_placeholders
from src.glance_attention.runlog import save_run_log, start_run_log
from src.glance_attention.schemas import CenterBias, load_aois
from src.glance_attention.study import Study, load_study
from src.glance_attention.validate import write_lock

REPO_ROOT = Path(__file__).resolve().parent.parent
SIZE = (200, 250)
CONFIG = 'placeholder = true\nbaseline = "A"\njitter_draws = 20\n'


def make_study(root: Path, size: tuple[int, int] = SIZE, count: int = 3) -> Study:
    """Write a placeholder study of `count` variants into `root` and return it loaded."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "study.toml").write_text(CONFIG, encoding="utf-8")
    make_placeholders(load_study(root), size, count)
    return load_study(root)


def fake_run(study: Study) -> None:
    """Lock the AOIs, save synthetic densities (extra mass on each price box) and a finished run log."""
    lock = write_lock(study)
    for variant in study.variants:
        width, height = Image.open(variant.image_path).size
        x0, y0, x1, y1 = load_aois(variant.aoi_path).aois["price"].boxes[0]
        for prior in CenterBias:
            density = np.ones((height, width))
            density[y0:y1, x0:x1] += 20 if prior == CenterBias.MIT1003 else 10
            path = study.density_path(variant.name, prior)
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, density / density.sum())
    centerbias = study.root / "fake_centerbias.bin"
    centerbias.write_bytes(b"not a real prior")
    save_run_log(study, start_run_log(study, lock, centerbias).model_copy(update={"status": "finished"}))


@pytest.fixture
def study(tmp_path: Path) -> Study:
    """Return a three-variant placeholder study in a temporary folder."""
    return make_study(tmp_path / "study")
