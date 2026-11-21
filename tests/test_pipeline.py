"""End-to-end tests of run, compare and report on saved synthetic densities; no model is loaded."""

import csv
import json
from pathlib import Path

import pytest

from src.glance_attention import CAVEAT, PLACEHOLDER_BANNER
from src.glance_attention.pipeline import compare_study, report_study, run_study
from src.glance_attention.preview import preview_study
from src.glance_attention.runlog import read_run_log, start_run_log
from src.glance_attention.study import Study, load_study
from src.glance_attention.validate import write_lock
from tests.conftest import fake_run, make_study

LONG_COLUMNS = ["tool", "variant", "aoi", "metric", "value", "scale", "run_date", "version"]


def _run_all(study: Study) -> Path:
    fake_run(study)
    run_study(study, skip_model=True)
    compare_study(study)
    report_study(study)
    return study.root / "output"


def _long_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == LONG_COLUMNS
        return list(reader)


def test_placeholder_study_marks_every_output(study: Study) -> None:
    out = _run_all(study)
    preview_study(study)
    files = [path for path in out.rglob("*") if path.is_file()]
    assert {path.name for path in files} >= {
        "PLACEHOLDER_A_aoi.csv",
        "PLACEHOLDER_summary.csv",
        "PLACEHOLDER_compare.csv",
        "PLACEHOLDER_verdict.csv",
        "PLACEHOLDER_jitter.csv",
        "PLACEHOLDER_jitter_stability.csv",
        "PLACEHOLDER_panel.png",
        "PLACEHOLDER_panel_no_centerbias.png",
        "PLACEHOLDER_A_heatmap.png",
        "PLACEHOLDER_A_aoi.png",
        "PLACEHOLDER_A_aois.png",
        "PLACEHOLDER_aoi_boxes.csv",
        "PLACEHOLDER_report.md",
        "PLACEHOLDER_cross_tool_long.csv",
        "PLACEHOLDER_run_log.json",
    }
    assert all(path.name.startswith("PLACEHOLDER_") for path in files)
    report = (out / "PLACEHOLDER_report.md").read_text(encoding="utf-8")
    assert PLACEHOLDER_BANNER.upper() in report
    assert CAVEAT in report
    assert all(row["version"].startswith("PLACEHOLDER") for row in _long_rows(out / "PLACEHOLDER_cross_tool_long.csv"))


def test_long_table_has_filled_deepgaze_rows_and_empty_template_rows(study: Study) -> None:
    rows = _long_rows(_run_all(study) / "PLACEHOLDER_cross_tool_long.csv")
    deepgaze = [row for row in rows if row["tool"] == "deepgaze_iie"]
    others = [row for row in rows if row["tool"] != "deepgaze_iie"]
    assert all(row["value"] != "" and row["run_date"] for row in deepgaze)
    assert {row["tool"] for row in others} == {"attention_insight", "neurons_predict"}
    assert all(row["value"] == "" for row in others)
    assert len(others) == 2 * 3 * (5 + 1)
    metrics = {row["metric"] for row in deepgaze}
    assert {"attention_pct", "attention_density", "aoi_rank", "first_look_rank", "clarity"} <= metrics
    assert {"attention_pct_no_centerbias", "attention_pct_delta_vs_baseline"} <= metrics
    price = [row for row in deepgaze if (row["aoi"], row["metric"]) == ("price", "attention_pct")]
    assert [row["variant"] for row in price] == ["A", "B", "C"]


def test_tables_are_identical_when_the_run_is_repeated(study: Study) -> None:
    out = _run_all(study)
    before = {path.name: path.read_bytes() for path in out.glob("*.csv")}
    run_study(study, skip_model=True)
    compare_study(study)
    report_study(study)
    assert before == {path.name: path.read_bytes() for path in out.glob("*.csv")}


def test_run_refuses_unlocked_and_changed_aois(study: Study) -> None:
    with pytest.raises(SystemExit, match="not locked yet"):
        run_study(study, skip_model=True)
    fake_run(study)
    path = study.root / "aois" / "A.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="changed since they were locked"):
        run_study(study, skip_model=True)
    write_lock(study)
    with pytest.raises(SystemExit, match="changed since the last model run"):
        run_study(study, skip_model=True)


def test_run_log_records_aois_before_the_model_and_notices_later_changes(study: Study) -> None:
    fake_run(study)
    first = read_run_log(study)
    assert first is not None
    assert first.aoi_lock.files["A"].sha256
    assert first.aoi_lock.locked_utc <= first.run_utc
    assert not first.has_aois_changed_since_a_run
    assert "/Users/" not in first.model_dump_json()
    path = study.root / "aois" / "A.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    second = start_run_log(study, write_lock(study), study.root / "fake_centerbias.bin")
    assert second.has_aois_changed_since_a_run
    assert len(second.past_runs) == 1


def test_real_images_swap_in_with_no_code_change(tmp_path: Path) -> None:
    """Four variants, other names, another size, not a placeholder: only files and config differ."""
    study = make_study(tmp_path / "real", size=(320, 180), count=4)
    names = {"A": "control", "B": "top_right", "C": "on_product", "D": "bottom_left"}
    for old, new in names.items():
        (study.root / "images" / f"{old}.png").rename(study.root / "images" / f"{new}.png")
        entry = json.loads((study.root / "aois" / f"{old}.json").read_text(encoding="utf-8"))
        entry["image"] = f"{new}.png"
        (study.root / "aois" / f"{new}.json").write_text(json.dumps(entry), encoding="utf-8")
        (study.root / "aois" / f"{old}.json").unlink()
    config = 'title = "Real ads"\nbaseline = "control"\njitter_draws = 5\n[[external_tools]]\nname = "expoze"\n'
    config += 'metrics = [{ metric = "attention_pct", level = "aoi", scale = "0-100" }]\n'
    (study.root / "study.toml").write_text(config, encoding="utf-8")
    out = _run_all(load_study(study.root))
    assert not any(path.name.startswith("PLACEHOLDER") for path in out.rglob("*"))
    rows = _long_rows(out / "cross_tool_long.csv")
    assert {row["variant"] for row in rows} == set(names.values())
    assert {row["tool"] for row in rows} == {"deepgaze_iie", "expoze"}
    assert not any("PLACEHOLDER" in row["version"] for row in rows)
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "PLACEHOLDER" not in report
    assert "baseline control" in report
