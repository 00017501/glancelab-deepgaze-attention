"""Generate placeholder stimuli and matching AOI files, so the pipeline can be built before the real ads exist."""

import json
import logging
from string import ascii_uppercase

from PIL import Image, ImageDraw

from src.glance_attention.schemas import Box
from src.glance_attention.study import Study
from src.glance_attention.visuals import load_font

logger = logging.getLogger(__name__)

# Fixed elements as fractions of the image `(x0, y0, x1, y1)`; fractions keep the layout at any size.
FIXED_ELEMENTS: dict[str, tuple[float, float, float, float]] = {
    "logo": (0.06, 0.05, 0.26, 0.12),
    "headline": (0.06, 0.16, 0.80, 0.24),
    "product": (0.20, 0.36, 0.80, 0.76),
}
# Price box size as fractions of the image; identical in every variant.
PRICE_SIZE = (0.22, 0.10)
# Top-left corner of the price box per variant, in order: bottom right (the conventional spot),
# top right, on the product's edge, bottom left, right of the product.
PRICE_POSITIONS = ((0.72, 0.84), (0.72, 0.05), (0.64, 0.56), (0.06, 0.84), (0.76, 0.28))
BACKGROUND = (236, 232, 224)
ELEMENT_COLOURS = {"logo": (40, 60, 90), "headline": (70, 70, 70), "product": (150, 150, 150)}
PRICE_COLOUR = (215, 30, 40)


def _pixels(fractions: tuple[float, float, float, float], width: int, height: int) -> Box:
    """Return a fractional box as integer pixels."""
    x0, y0, x1, y1 = fractions
    return (round(x0 * width), round(y0 * height), round(x1 * width), round(y1 * height))


def _price_box(position: tuple[float, float], width: int, height: int) -> Box:
    """Return the price box at `position`; the pixel size is the same for every position."""
    x0, y0 = round(position[0] * width), round(position[1] * height)
    return (x0, y0, x0 + round(PRICE_SIZE[0] * width), y0 + round(PRICE_SIZE[1] * height))


def _label(draw: ImageDraw.ImageDraw, box: Box, text: str) -> None:
    """Write white text in the middle of a box, sized to the box height."""
    font = load_font(max(10, (box[3] - box[1]) // 2))
    draw.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text, fill=(255, 255, 255), font=font, anchor="mm")


def draw_variant(size: tuple[int, int], boxes: dict[str, Box]) -> Image.Image:
    """Return one placeholder ad: plain background, grey product, logo block, headline bar and price box."""
    image = Image.new("RGB", size, BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(boxes["product"], radius=size[0] // 20, fill=ELEMENT_COLOURS["product"])
    for name in ("logo", "headline"):
        draw.rectangle(boxes[name], fill=ELEMENT_COLOURS[name])
        _label(draw, boxes[name], name.upper())
    draw.rectangle(boxes["price"], fill=PRICE_COLOUR)
    _label(draw, boxes["price"], "PRICE")
    return image


def make_placeholders(study: Study, size: tuple[int, int], count: int) -> list[str]:
    """Write `count` placeholder variants (A, B, ...) and their AOI files into the study; return their names."""
    if not study.config.placeholder:
        msg = f"{study.root} is not marked `placeholder = true` in study.toml; refusing to write placeholder files"
        raise SystemExit(msg)
    if not 1 <= count <= len(PRICE_POSITIONS):
        msg = f"can generate 1 to {len(PRICE_POSITIONS)} placeholder variants, not {count}"
        raise SystemExit(msg)
    width, height = size
    fixed = {name: _pixels(fractions, width, height) for name, fractions in FIXED_ELEMENTS.items()}
    names = list(ascii_uppercase[:count])
    for folder in ("images", "aois"):
        (study.root / folder).mkdir(parents=True, exist_ok=True)
    for name, position in zip(names, PRICE_POSITIONS, strict=False):
        boxes = {"price": _price_box(position, width, height), **fixed}
        draw_variant(size, boxes).save(study.root / "images" / f"{name}.png")
        entry = {
            "_note": "PLACEHOLDER AOIs written by the placeholder generator. Boxes are [x0, y0, x1, y1] in pixels.",
            "image": f"{name}.png",
            "aois": {aoi: {"type": aoi, "boxes": [list(box)]} for aoi, box in boxes.items()},
        }
        (study.root / "aois" / f"{name}.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        logger.info("placeholder_written variant=%s size=%dx%d price_box=%s", name, width, height, list(boxes["price"]))
    return names
