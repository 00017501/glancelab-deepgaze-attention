"""The run log: everything needed to say which model, settings, images and AOIs produced a set of outputs."""

import hashlib
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from PIL import Image
from pydantic import BaseModel

from src.glance_attention import CAVEAT, PIPELINE_VERSION
from src.glance_attention.config import CONFIG_FILE_NAME
from src.glance_attention.model import DEVICE, MODEL_NAME
from src.glance_attention.study import Study, sha256_of
from src.glance_attention.validate import AoiLock

DEEPGAZE_DIR = Path("third_party/DeepGaze")
# File name of the DeepGaze IIE weights inside the torch hub cache.
WEIGHTS_FILE_NAME = "deepgaze2e.pth"
LIBRARIES = ("torch", "torchvision", "numpy", "scipy", "pillow", "pydantic", "deepgaze_pytorch")
UNKNOWN = "unknown"


class ImageRecord(BaseModel):
    """One stimulus as it was when the model ran."""

    file: str
    width: int
    height: int
    sha256: str


class PastRun(BaseModel):
    """An earlier run on this study and the fingerprint of the AOI set it used."""

    run_utc: str
    aoi_set_sha256: str


class RunLog(BaseModel):
    """`run_log.json`; written before the model loads and completed when the run ends."""

    caveat: str = CAVEAT
    status: str
    is_placeholder: bool
    study_title: str
    run_utc: str
    run_date: str
    pipeline_version: str = PIPELINE_VERSION
    git_commit: str
    is_git_dirty: bool
    model: str = MODEL_NAME
    deepgaze_commit: str
    weights_file: str = WEIGHTS_FILE_NAME
    weights_sha256: str
    device: str = DEVICE
    centerbias_primary: str = "mit1003 template, resized to the image (nearest), renormalised"
    centerbias_sensitivity: str = "uniform (no centre bias)"
    centerbias_file: str
    centerbias_sha256: str
    python: str
    libraries: dict[str, str]
    baseline: str
    config_sha256: str
    jitter_pct: float
    jitter_draws: int
    jitter_seed: int
    product_drop_threshold_pct: float
    images: dict[str, ImageRecord]
    aoi_lock: AoiLock
    aoi_set_sha256: str
    # True when an earlier run on this study used different AOIs: the boxes were not fixed first.
    has_aois_changed_since_a_run: bool
    past_runs: list[PastRun]


def _git(*args: str, cwd: Path | None = None) -> str:
    """Return the output of a git command, or `unknown` when git or the repository is unavailable."""
    try:
        done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)  # noqa: S603, S607
    except (OSError, subprocess.CalledProcessError):
        return UNKNOWN
    return done.stdout.strip()


def _library_versions() -> dict[str, str]:
    """Return the installed version of each library the numbers depend on."""
    versions = {}
    for name in LIBRARIES:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = UNKNOWN
    return versions


def _weights_sha256() -> str:
    """Return the hash of the cached model weights; `unknown` before the first download."""
    import torch

    path = Path(torch.hub.get_dir()) / "checkpoints" / WEIGHTS_FILE_NAME
    return sha256_of(path) if path.exists() else UNKNOWN


def aoi_set_sha256(lock: AoiLock) -> str:
    """Return one fingerprint for the whole locked AOI set."""
    joined = "\n".join(f"{name}:{locked.sha256}" for name, locked in sorted(lock.files.items()))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def read_run_log(study: Study) -> RunLog | None:
    """Return the study's run log, or `None` before the first run."""
    path = study.output("run_log.json")
    return RunLog.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def start_run_log(study: Study, lock: AoiLock, centerbias_path: Path) -> RunLog:
    """Build the run log from the current state and save it, before any model work."""
    previous, now = read_run_log(study), datetime.now(UTC)
    past_runs = (
        []
        if previous is None
        else [*previous.past_runs, PastRun(**previous.model_dump(include={"run_utc", "aoi_set_sha256"}))]
    )
    fingerprint = aoi_set_sha256(lock)
    images = {}
    for variant in study.variants:
        width, height = Image.open(variant.image_path).size
        images[variant.name] = ImageRecord(
            file=f"images/{variant.image_path.name}", width=width, height=height, sha256=sha256_of(variant.image_path)
        )
    config_path = study.root / CONFIG_FILE_NAME
    log = RunLog(
        status="started",
        is_placeholder=study.config.placeholder,
        study_title=study.config.title,
        run_utc=now.isoformat(timespec="seconds"),
        run_date=now.date().isoformat(),
        git_commit=_git("rev-parse", "HEAD"),
        is_git_dirty=_git("status", "--porcelain") not in ("", UNKNOWN),
        deepgaze_commit=_git("rev-parse", "HEAD", cwd=DEEPGAZE_DIR) if DEEPGAZE_DIR.is_dir() else UNKNOWN,
        weights_sha256=_weights_sha256(),
        centerbias_file=centerbias_path.name,
        centerbias_sha256=sha256_of(centerbias_path),
        python=platform.python_version(),
        libraries=_library_versions(),
        baseline=study.baseline,
        config_sha256=sha256_of(config_path) if config_path.exists() else "no study.toml (defaults)",
        jitter_pct=study.config.jitter_pct,
        jitter_draws=study.config.jitter_draws,
        jitter_seed=study.config.jitter_seed,
        product_drop_threshold_pct=study.config.product_drop_threshold_pct,
        images=images,
        aoi_lock=lock,
        aoi_set_sha256=fingerprint,
        has_aois_changed_since_a_run=any(run.aoi_set_sha256 != fingerprint for run in past_runs),
        past_runs=past_runs,
    )
    save_run_log(study, log)
    return log


def save_run_log(study: Study, log: RunLog) -> None:
    """Write the run log to the study's output folder."""
    path = study.output("run_log.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(log.model_dump_json(indent=2) + "\n", encoding="utf-8")
