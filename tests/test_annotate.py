"""Tests for the AI AOI proposal helper; the model is a local function, so no network is used."""

import json
import re
from pathlib import Path

import pytest
from PIL import Image
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.profiles import ModelProfile

from src.glance_attention.annotate.annotate import MAX_EDGE_PX, AnnotationRequest, annotate, prepare_image
from src.glance_attention.annotate.apply import apply_proposal
from src.glance_attention.annotate.reply import AoiReply, to_aois
from src.glance_attention.schemas import load_aois
from src.glance_attention.study import Study, load_study
from src.glance_attention.validate import check_study
from tests.conftest import REPO_ROOT

PROMPT_FILE = REPO_ROOT / "prompts" / "aoi" / "annotation.txt"


def _box(x0: int, y0: int, x1: int, y1: int) -> dict[str, int]:
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _reply(price: dict[str, int], logo: dict[str, int] | None = None) -> dict[str, object]:
    return {
        "aois": [
            {"name": "price", "type": "price", "boxes": [price]},
            {"name": "product", "type": "product", "boxes": [_box(40, 90, 160, 190)]},
            {"name": "logo", "type": "logo", "boxes": [logo or _box(12, 12, 52, 30)]},
            {"name": "headline", "type": "headline", "boxes": [_box(12, 40, 160, 60)]},
        ]
    }


def _fake_model(reply: dict[str, object], seen: list[str] | None = None) -> FunctionModel:
    """Return a model that answers every request with `reply` and records the prompt text it was given."""

    def respond(messages: list[ModelMessage], _info: AgentInfo) -> ModelResponse:
        if seen is not None:
            seen.extend(part.content[0] for part in messages[-1].parts if hasattr(part, "content"))
        return ModelResponse(parts=[TextPart(json.dumps(reply))], model_name="fake-model")

    return FunctionModel(respond, model_name="fake-model", profile=ModelProfile(supports_json_schema_output=True))


def _image(tmp_path: Path, size: tuple[int, int]) -> Path:
    path = tmp_path / "A.png"
    Image.new("RGB", size, (30, 30, 30)).save(path)
    return path


def test_prompt_file_matches_the_published_prompt() -> None:
    published = (REPO_ROOT / "docs" / "AI_USE_AND_PROMPTS.md").read_text(encoding="utf-8")
    block = re.search(r"### 2b\..*?```\n(.*?)```", published, re.DOTALL)
    assert block is not None
    assert block.group(1) == PROMPT_FILE.read_text(encoding="utf-8")


def test_prepare_image_downscales_only_large_images(tmp_path: Path) -> None:
    _, original, sent, scale = prepare_image(_image(tmp_path, (900, 1800)))
    assert original == (900, 1800)
    assert max(sent) == MAX_EDGE_PX
    assert scale == pytest.approx(MAX_EDGE_PX / 1800)
    assert prepare_image(_image(tmp_path, (900, 1199)))[3] == 1.0


def test_to_aois_scales_boxes_back_and_clamps() -> None:
    reply = AoiReply.model_validate({"aois": [{"name": "logo", "type": "logo", "boxes": [_box(50, 50, 2000, 100)]}]})
    assert to_aois(reply, 0.5, 900, 1800)["logo"].boxes == [(100, 100, 900, 200)]


def test_annotate_writes_proposal_and_record_with_filled_prompt(tmp_path: Path) -> None:
    seen: list[str] = []
    request = AnnotationRequest("study__A", _image(tmp_path, (200, 250)), PROMPT_FILE, "high")
    record = annotate(_fake_model(_reply(_box(150, 200, 190, 230)), seen), request, tmp_path / "staging")
    entry = json.loads((tmp_path / "staging" / "study__A.json").read_text(encoding="utf-8"))
    meta = (tmp_path / "staging" / "study__A.meta.json").read_text(encoding="utf-8")
    assert entry["image"] == "A.png"
    assert entry["aois"]["price"] == {"type": "price", "boxes": [[150, 200, 190, 230]]}
    assert "The image is 200 x 250 pixels." in seen[0]
    assert record.model_used == "fake-model"
    assert record.problems == []
    assert str(tmp_path) not in meta


def test_annotate_never_overwrites_and_never_stores_the_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-secret")
    request = AnnotationRequest("study__A", _image(tmp_path, (200, 250)), PROMPT_FILE, "high")
    annotate(_fake_model(_reply(_box(150, 200, 190, 230))), request, tmp_path)
    assert "sk-ant-test-secret" not in (tmp_path / "study__A.meta.json").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        annotate(_fake_model(_reply(_box(150, 200, 190, 230))), request, tmp_path)


def _emptied(study: Study) -> Study:
    for path in (study.root / "aois").glob("*.json"):
        path.unlink()
    return load_study(study.root)


def _propose(study: Study, name: str, reply: dict[str, object], staging: Path) -> Path:
    variant = next(variant for variant in study.variants if variant.name == name)
    annotate(_fake_model(reply), AnnotationRequest(f"s__{name}", variant.image_path, PROMPT_FILE, "high"), staging)
    return staging / f"s__{name}.json"


def test_apply_copies_fixed_aois_from_the_baseline(study: Study, tmp_path: Path) -> None:
    study, staging = _emptied(study), tmp_path / "staging"
    variants = {variant.name: variant for variant in study.variants}
    with pytest.raises(SystemExit, match="apply the baseline A first"):
        apply_proposal(study, variants["B"], _propose(study, "B", _reply(_box(150, 12, 190, 42)), staging))
    apply_proposal(study, variants["A"], _propose(study, "A", _reply(_box(150, 200, 190, 230)), staging))
    drifted_logo = _reply(_box(100, 150, 140, 180), logo=_box(14, 14, 54, 32))
    apply_proposal(study, variants["B"], staging / "s__B.json")
    apply_proposal(study, variants["C"], _propose(study, "C", drifted_logo, staging))
    assert load_aois(variants["C"].aoi_path).aois["logo"] == load_aois(variants["A"].aoi_path).aois["logo"]
    assert load_aois(variants["C"].aoi_path).aois["price"].boxes == [(100, 150, 140, 180)]
    assert check_study(study).errors == []
    with pytest.raises(SystemExit, match="never replaced silently"):
        apply_proposal(study, variants["A"], staging / "s__A.json")


def test_apply_refuses_boxes_that_fail_the_checks(study: Study, tmp_path: Path) -> None:
    study = _emptied(study)
    overlapping = _reply(_box(150, 200, 190, 230), logo=_box(12, 12, 160, 50))
    entry = _propose(study, "A", overlapping, tmp_path / "staging")
    with pytest.raises(SystemExit, match="logo and headline overlap"):
        apply_proposal(study, study.variants[0], entry)


def test_real_anthropic_request_shape(tmp_path: Path) -> None:
    import httpx2 as httpx
    from anthropic import AsyncAnthropic
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.providers.anthropic import AnthropicProvider

    sent: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        body = {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": json.dumps(_reply(_box(150, 200, 190, 230)))}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        return httpx.Response(200, json=body)

    client = AsyncAnthropic(
        api_key="sk-ant-test", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    model = AnthropicModel("claude-opus-5-5", provider=AnthropicProvider(anthropic_client=client))
    record = annotate(model, AnnotationRequest("s__A", _image(tmp_path, (200, 250)), PROMPT_FILE, "high"), tmp_path)
    (payload,) = sent
    assert payload["model"] == "claude-opus-5-5"
    assert payload["output_config"]["effort"] == "high"
    assert payload["output_config"]["format"]["type"] == "json_schema"
    assert not {"temperature", "top_p", "top_k"} & payload.keys()
    assert any(block.get("type") == "image" for block in payload["messages"][0]["content"])
    assert record.request_id == "msg_test"
    assert record.model_used == "claude-opus-5-5"
