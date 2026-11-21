"""Smoke test with the real model; skipped until setup.sh has fetched the centre-bias file."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tests.conftest import REPO_ROOT

CENTERBIAS = REPO_ROOT / "centerbias_mit1003.npy"


@pytest.mark.slow
@pytest.mark.skipif(not CENTERBIAS.exists(), reason="run setup.sh first")
def test_deepgaze_puts_the_peak_on_a_salient_square_under_both_priors(tmp_path: Path) -> None:
    from src.glance_attention.model import DeepGazeRunner

    pixels = np.full((768, 1024, 3), 128, np.uint8)
    pixels[200:350, 650:800] = (255, 0, 0)
    path = tmp_path / "square.png"
    Image.fromarray(pixels).save(path)
    runner = DeepGazeRunner()
    for centerbias in (CENTERBIAS, None):
        density = runner.predict_density(path, centerbias)
        assert density.shape == (768, 1024)
        assert density.sum() == pytest.approx(1.0)
        peak_y, peak_x = np.unravel_index(density.argmax(), density.shape)
        assert 150 <= peak_y <= 400
        assert 600 <= peak_x <= 850
