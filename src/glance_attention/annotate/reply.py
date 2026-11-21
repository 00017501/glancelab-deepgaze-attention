"""The model's structured reply and its conversion to the AOIs of one variant."""

from typing import Literal

from pydantic import BaseModel

from src.glance_attention.schemas import Aoi, Box

# The AOI types the prompt allows; `rest` is computed, never drawn.
type ReplyType = Literal["price", "product", "logo", "headline", "text", "visual"]


class ReplyBox(BaseModel):
    """One rectangle in the pixel space of the image the model was shown."""

    x0: int
    y0: int
    x1: int
    y1: int


class ReplyAoi(BaseModel):
    """One named AOI with its type and rectangles."""

    name: str
    type: ReplyType
    boxes: list[ReplyBox]


class AoiReply(BaseModel):
    """The whole reply; a list rather than a name-keyed object, which structured outputs can't express."""

    aois: list[ReplyAoi]


def to_aois(reply: AoiReply, scale: float, width: int, height: int) -> dict[str, Aoi]:
    """Map boxes from the shown image back to original pixels (divide by `scale`) and clamp them to the image."""

    def original(box: ReplyBox) -> Box:
        x0, y0, x1, y1 = (round(value / scale) for value in (box.x0, box.y0, box.x1, box.y1))
        return (max(0, min(x0, width)), max(0, min(y0, height)), max(0, min(x1, width)), max(0, min(y1, height)))

    return {
        aoi.name: Aoi.model_validate({"type": aoi.type, "boxes": [original(box) for box in aoi.boxes]})
        for aoi in reply.aois
    }
