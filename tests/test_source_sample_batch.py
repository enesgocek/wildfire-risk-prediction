import importlib.util
import json
from pathlib import Path

import pytest

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.target_admission import specification


@pytest.fixture
def batch(monkeypatch, tmp_path):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "batch_review_test", folder / "audit_source_sample_batch.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    monkeypatch.setattr(result, "ROOT", tmp_path)
    monkeypatch.setattr(result, "BASE", tmp_path / "outputs/reports/dataset")
    return result


def point_result(batch):
    folder = batch.BASE / "source_sample_point_v1/test"
    folder.mkdir(parents=True)
    path = folder / "readback.json"
    data = batch.ROOT / "native.nc"
    code = batch.ROOT / "auditor.py"
    plan = batch.ROOT / "plan.json"
    for p in (data, code, plan):
        p.write_text("test fixture")
    result = {
        "archive_row": "WF1207",
        "scope": "one_frozen_source_row_single_swath_diagnostic_only",
        "gate": specification(),
        "L_memberships_created": 0,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "network_used": False,
        "input_sha256": {p.name: digest(p) for p in (data, plan)},
        "code_sha256": {code.name: digest(code)},
    }
    path.write_text(json.dumps(result))
    return path, result, data, code, plan


def test_current_exact_diagnostic_is_reusable(batch):
    path, result, _, _, plan = point_result(batch)
    assert batch.verify_result(path, "WF1207", plan_path=plan) == result


@pytest.mark.parametrize(
    "mutation", ["raw", "code", "row", "gate", "labels", "training", "merge", "network"]
)
def test_stale_bytes_wrong_row_or_opened_gates_cannot_be_reused(batch, mutation):
    path, result, data, code, _ = point_result(batch)
    if mutation == "raw":
        data.write_text("changed")
    elif mutation == "code":
        code.write_text("changed")
    elif mutation == "row":
        result["archive_row"] = "WF1300"
    elif mutation == "gate":
        result["gate"]["negative_label_permitted"] = True
    else:
        key = {
            "labels": "labels_created",
            "training": "model_trained",
            "merge": "final_merge_performed",
            "network": "network_used",
        }[mutation]
        result[key] = True
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError):
        batch.verify_result(path, "WF1207")


def test_a_different_native_plan_is_not_silently_substituted(batch):
    path, _, _, _, _ = point_result(batch)
    alternate = batch.ROOT / "alternate_plan.json"
    alternate.write_text("another plan")
    with pytest.raises(KeyError):
        batch.verify_result(path, "WF1207", plan_path=alternate)


@pytest.fixture
def summary(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "source_summary_test", folder / "summarize_source_sample_native.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_missing_spatial_support_is_never_clear_or_negative(summary):
    result = summary.point_codes({"local_scan_contexts": []})
    assert result["point_mask_codes"] == []
    assert not result["point_support_found"] and not result["all_point_support_mask5"]
    assert not result["is_negative_label"]


def test_overlapping_scans_keep_every_class_without_a_best_scan_choice(summary):
    result = summary.point_codes(
        {
            "local_scan_contexts": [
                {"contexts": [{"point_mask_codes": [5]}]},
                {"contexts": [{"point_mask_codes": [4, 8]}]},
            ]
        }
    )
    assert result["point_mask_codes"] == [4, 5, 8]
    assert result["point_fire_mask_present_in_reviewed_pair"]
    assert result["point_cloud_mask_present_in_reviewed_pair"]
    assert not result["all_point_support_mask5"] and not result["is_negative_label"]


def test_mask5_support_remains_only_a_single_pair_diagnostic(summary):
    result = summary.point_codes(
        {
            "local_scan_contexts": [
                {"contexts": [{"point_mask_codes": [5]}, {"point_mask_codes": [5]}]}
            ]
        }
    )
    assert result["all_point_support_mask5"] and not result["is_negative_label"]
    assert not result["point_fire_mask_present_in_reviewed_pair"]
