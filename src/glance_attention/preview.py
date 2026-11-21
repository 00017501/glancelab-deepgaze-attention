"""Draw the AOI boxes on the plain images and list them in pixels and %, for checking before the model runs."""

import logging

from PIL import Image
from pydantic import BaseModel

from src.glance_attention.schemas import load_aois
from src.glance_attention.study import Study
from src.glance_attention.tables import write_csv
from src.glance_attention.visuals import aoi_overlay, stamp

logger = logging.getLogger(__name__)


class BoxRow(BaseModel):
    """One box of `aoi_boxes.csv`, in pixels and as % of the image, ready to redraw in another tool."""

    variant: str
    aoi: str
    type: str
    box: int
    x0: int
    y0: int
    x1: int
    y1: int
    left_pct: float
    top_pct: float
    width_pct: float
    height_pct: float


def preview_study(study: Study) -> list[BoxRow]:
    """Write `output/preview/<variant>_aois.png` per variant and `aoi_boxes.csv`; return the box rows."""
    rows = []
    for variant in study.variants:
        if not variant.aoi_path.exists():
            logger.warning("preview_skipped variant=%s reason=no_aoi_file", variant.name)
            continue
        image = Image.open(variant.image_path).convert("RGB")
        aois = load_aois(variant.aoi_path).aois
        overlay = aoi_overlay(image, aois, {name: name for name in aois})
        path = study.output("preview", f"{variant.name}_aois.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp(
            overlay, is_placeholder=study.config.placeholder, title=f"AOI preview: {variant.name}", has_caveat=False
        ).save(path)
        for name, aoi in aois.items():
            for index, (x0, y0, x1, y1) in enumerate(aoi.boxes, 1):
                row = BoxRow(
                    variant=variant.name,
                    aoi=name,
                    type=aoi.type,
                    box=index,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    left_pct=100 * x0 / image.width,
                    top_pct=100 * y0 / image.height,
                    width_pct=100 * (x1 - x0) / image.width,
                    height_pct=100 * (y1 - y0) / image.height,
                )
                rows.append(row)
                logger.info(
                    "aoi_box variant=%s aoi=%s px=%s left=%.1f%% top=%.1f%% width=%.1f%% height=%.1f%%",
                    variant.name, name, [x0, y0, x1, y1], row.left_pct, row.top_pct, row.width_pct, row.height_pct,
                )  # fmt: skip
    write_csv(study.output("preview", "aoi_boxes.csv"), rows, BoxRow)
    return rows
