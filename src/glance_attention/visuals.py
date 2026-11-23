"""Heatmaps, AOI overlays, the side-by-side panel and the stamps, drawn with numpy and PIL only."""

import numpy as np
import numpy.typing as npt
from PIL import Image, ImageDraw, ImageFont

from src.glance_attention import CAVEAT, PLACEHOLDER_BANNER
from src.glance_attention.schemas import Aoi, AoiType

# Inferno-like colour stops; inlined so the visuals need no plotting library.
COLORMAP_STOPS = np.array(
    [
        [0, 0, 4],
        [40, 11, 84],
        [101, 21, 110],
        [159, 42, 99],
        [212, 72, 66],
        [245, 125, 21],
        [250, 193, 39],
        [252, 255, 164],
    ],
    float,
)
# Box and label colour per AOI type; white for anything unlisted.
TYPE_COLOURS: dict[AoiType, tuple[int, int, int]] = {
    AoiType.PRICE: (255, 230, 0),
    AoiType.PRODUCT: (0, 255, 120),
    AoiType.LOGO: (0, 200, 255),
    AoiType.HEADLINE: (200, 70, 255),
    AoiType.TEXT: (255, 140, 0),
    AoiType.VISUAL: (160, 120, 255),
}
# Bold fonts tried in order; the names cover Linux, Windows and macOS.
FONT_CANDIDATES = (
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
    "Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
)
# Panel tiles are scaled to this height so any number of variants stays a manageable file.
PANEL_TILE_HEIGHT = 900
PANEL_GAP = 16
BANNER_COLOUR = (200, 0, 0)


def colormap(values: npt.NDArray[np.float64]) -> npt.NDArray[np.uint8]:
    """Map values in 0..1 to RGB by linear interpolation between the colour stops."""
    scaled = np.clip(values, 0, 1) * (len(COLORMAP_STOPS) - 1)
    index = np.minimum(scaled.astype(int), len(COLORMAP_STOPS) - 2)
    fraction = (scaled - index)[..., None]
    return (COLORMAP_STOPS[index] * (1 - fraction) + COLORMAP_STOPS[index + 1] * fraction).astype(np.uint8)


def heat_overlay(image: Image.Image, density: npt.NDArray[np.float64], scale_max: float) -> Image.Image:
    """Blend the density heatmap over a dimmed copy of the image.

    `scale_max` is the density shown as the hottest colour; passing one value for all variants
    makes their colours comparable.
    """
    values = np.clip(density / scale_max, 0, 1)
    values = values**0.4  # gamma so mid-level attention stays visible
    rgb = colormap(values).astype(float)
    base = np.asarray(image.convert("RGB")).astype(float) * 0.6
    opacity = (0.8 * np.clip(values * 2.0, 0, 1))[..., None]
    return Image.fromarray((base * (1 - opacity) + rgb * opacity).astype(np.uint8))


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Return the first available bold font at `size`, or PIL's built-in font."""
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def aoi_overlay(image: Image.Image, aois: dict[str, Aoi], labels: dict[str, str]) -> Image.Image:
    """Draw each AOI's boxes and its label on a copy of the image."""
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    font = load_font(max(12, canvas.width // 56))
    for name, aoi in aois.items():
        colour = TYPE_COLOURS.get(aoi.type, (255, 255, 255))
        for box in aoi.boxes:
            draw.rectangle(box, outline=colour, width=4)
        x0, y0 = aoi.boxes[0][:2]
        text_w, text_h = draw.textbbox((0, 0), labels[name], font=font)[2:]
        # Label sits above the first box, or inside it when there is no room above.
        text_y = y0 - text_h - 8 if y0 - text_h - 8 > 0 else y0 + 4
        draw.rectangle([x0, text_y, x0 + text_w + 10, text_y + text_h + 6], fill=(0, 0, 0))
        draw.text((x0 + 5, text_y + 2), labels[name], fill=colour, font=font)
    return canvas


def _strip(width: int, text: str, fill: tuple[int, int, int]) -> Image.Image:
    """Return a full-width strip with centred white text, shrunk until it fits."""
    size = max(12, width // 36)
    font = load_font(size)
    while size > 8 and font.getlength(text) > width - 16:  # noqa: PLR2004
        size -= 1
        font = load_font(size)
    strip = Image.new("RGB", (width, round(size * 1.8)), fill)
    ImageDraw.Draw(strip).text((width / 2, strip.height / 2), text, fill=(255, 255, 255), font=font, anchor="mm")
    return strip


def stamp(
    image: Image.Image, *, is_placeholder: bool, title: str | None = None, has_caveat: bool = True
) -> Image.Image:
    """Return the image with the caveat below it, an optional title above, and the placeholder banner on top."""
    above = [_strip(image.width, PLACEHOLDER_BANNER.upper(), BANNER_COLOUR)] if is_placeholder else []
    if title is not None:
        above.append(_strip(image.width, title, (40, 40, 40)))
    parts = [*above, image, *([_strip(image.width, CAVEAT, (0, 0, 0))] if has_caveat else [])]
    canvas = Image.new("RGB", (image.width, sum(part.height for part in parts)), (0, 0, 0))
    top = 0
    for part in parts:
        canvas.paste(part, (0, top))
        top += part.height
    return canvas


def panel(tiles: list[tuple[str, Image.Image]], *, is_placeholder: bool, title: str) -> Image.Image:
    """Return all tiles side by side at one height, each under its own title, stamped as one image."""
    titled = []
    for tile_title, image in tiles:
        scale = min(1.0, PANEL_TILE_HEIGHT / image.height)
        resized = image.resize((round(image.width * scale), round(image.height * scale)))
        header = _strip(resized.width, tile_title, (40, 40, 40))
        tile = Image.new("RGB", (resized.width, header.height + resized.height))
        tile.paste(header, (0, 0))
        tile.paste(resized, (0, header.height))
        titled.append(tile)
    width = sum(tile.width for tile in titled) + PANEL_GAP * (len(titled) + 1)
    canvas = Image.new("RGB", (width, max(tile.height for tile in titled) + 2 * PANEL_GAP), (255, 255, 255))
    left = PANEL_GAP
    for tile in titled:
        canvas.paste(tile, (left, PANEL_GAP))
        left += tile.width + PANEL_GAP
    return stamp(canvas, is_placeholder=is_placeholder, title=title)
