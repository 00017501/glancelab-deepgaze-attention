"""Tests for the pre-model checks and the AOI lock."""

import json
from pathlib import Path

from PIL import Image

from src.glance_attention.study import Study, load_study
from src.glance_attention.validate import check_study, lock_problem, read_lock, write_lock


def _edit_aois(study: Study, variant: str, aoi: str, box: list[int]) -> None:
    path = study.root / "aois" / f"{variant}.json"
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry["aois"][aoi]["boxes"] = [box]
    path.write_text(json.dumps(entry), encoding="utf-8")


def test_generated_study_is_valid_and_reports_the_price_on_the_product(study: Study) -> None:
    findings = check_study(study)
    assert findings.errors == []
    assert len(findings.warnings) == 1
    assert "C: 'price' covers" in findings.warnings[0]


def test_images_of_different_sizes_are_an_error_that_lists_each_size(study: Study) -> None:
    Image.new("RGB", (210, 250)).save(study.root / "images" / "B.png")
    errors = check_study(load_study(study.root)).errors
    assert any("not all the same size" in error and "B=210x250" in error for error in errors)


def test_a_fixed_aoi_that_differs_from_the_baseline_is_an_error(study: Study) -> None:
    _edit_aois(study, "B", "logo", [12, 12, 50, 30])
    assert any("B: fixed AOIs differ from baseline A" in error for error in check_study(study).errors)


def test_a_price_box_of_another_size_is_an_error(study: Study) -> None:
    _edit_aois(study, "B", "price", [144, 12, 150, 20])
    assert any("B: 'price' box size" in error for error in check_study(study).errors)


def test_missing_and_orphaned_aoi_files_are_errors(study: Study) -> None:
    (study.root / "aois" / "C.json").rename(study.root / "aois" / "Z.json")
    errors = check_study(study).errors
    assert any("C: no AOI file" in error for error in errors)
    assert any("aois/Z.json has no image" in error for error in errors)


def test_boxes_outside_the_image_and_overlapping_fixed_aois_are_errors(study: Study) -> None:
    for variant in "ABC":
        _edit_aois(study, variant, "logo", [12, 12, 260, 50])
    errors = check_study(study).errors
    assert any("extends past the 200x250 image" in error for error in errors)
    assert any("logo and headline overlap" in error for error in errors)


def test_an_unknown_baseline_and_a_single_variant_are_errors(tmp_path: Path) -> None:
    (tmp_path / "images").mkdir()
    Image.new("RGB", (50, 50)).save(tmp_path / "images" / "only.png")
    (tmp_path / "study.toml").write_text('baseline = "A"\n', encoding="utf-8")
    errors = check_study(load_study(tmp_path)).errors
    assert any("needs at least 2" in error for error in errors)
    assert any("baseline 'A' is not among" in error for error in errors)


def test_lock_keeps_its_time_until_an_aoi_file_changes(study: Study) -> None:
    assert lock_problem(study) == "the AOIs are not locked yet; run `validate` first"
    first = write_lock(study)
    assert lock_problem(study) is None
    assert write_lock(study) == first == read_lock(study.lock_path)
    _edit_aois(study, "A", "price", [144, 210, 188, 235])
    assert "changed since they were locked" in (lock_problem(study) or "")
    assert write_lock(study).files["A"].sha256 != first.files["A"].sha256
