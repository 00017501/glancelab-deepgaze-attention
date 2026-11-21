"""DeepGaze IIE inference: the prior (centre bias or none) and the fixation density per image."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
from PIL import Image

if TYPE_CHECKING:
    import torch

logger = logging.getLogger(__name__)

MODEL_NAME = "DeepGaze IIE"
# The numbers in the report come from the CPU; other devices can differ in the last digits.
DEVICE = "cpu"


def load_centerbias(path: Path | None, height: int, width: int) -> npt.NDArray[np.float32]:
    """Return the log-density prior for an image: the template at `path` resized, or uniform for `None`."""
    if path is None:
        centerbias = np.zeros((height, width), np.float32)
    else:
        template = np.load(path).astype(np.float32)
        centerbias = np.array(Image.fromarray(template).resize((width, height), Image.NEAREST))
    peak = centerbias.max()
    # Subtract logsumexp so exp(centerbias) sums to 1.
    return centerbias - (peak + np.log(np.exp(centerbias - peak).sum()))


class DeepGazeRunner:
    """Run DeepGaze IIE, loading the pretrained model once on first use."""

    def __init__(self, device: str = DEVICE) -> None:
        self._device = device
        self._model: torch.nn.Module | None = None

    def predict_density(self, image_path: Path, centerbias_path: Path | None) -> npt.NDArray[np.float64]:
        """Return the fixation density of the image under the given prior; it sums to 1."""
        import torch

        image = np.array(Image.open(image_path).convert("RGB"))
        height, width = image.shape[:2]
        centerbias = load_centerbias(centerbias_path, height, width)
        with torch.no_grad():
            image_tensor = torch.tensor(image.transpose(2, 0, 1)[None].astype(np.float32)).to(self._device)
            centerbias_tensor = torch.tensor(centerbias[None]).to(self._device)
            log_density = self._get_model()(image_tensor, centerbias_tensor)[0, 0].cpu().numpy().astype(np.float64)
        density = np.exp(log_density)
        return density / density.sum()

    def _get_model(self) -> "torch.nn.Module":
        """Return the cached model, loading the pretrained weights on the first call."""
        if self._model is None:
            import deepgaze_pytorch

            logger.info("model_loading name=%s device=%s", MODEL_NAME, self._device)
            self._model = deepgaze_pytorch.DeepGazeIIE(pretrained=True).to(self._device).eval()
        return self._model
