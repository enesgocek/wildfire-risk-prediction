"""Synthetic receipts only: no user approval receipt or real training target is created."""

import copy
import json

import pytest

from wildfire_risk_prediction.dataset_execution import (
    PART_VERSION,
    file_hash,
    preflight_training_merge,
    public_file,
    verify_final_part_files,
)
from wildfire_risk_prediction.final_merge_gate import PARTS, review_digest


def fixture(root):
    folder = root / "outputs/reports/synthetic"
    folder.mkdir(parents=True)
    leaf = folder / "sample.csv"
    leaf.write_text("synthetic_only\n1\n", encoding="utf-8")
    review = {
        "status": "all_parts_final_review_passed",
        "scientific_protocol_status": "accepted",
        "split": "train_2018_2023",
        "final_test_accessed": False,
        "parts": {},
    }
    for part in PARTS:
        manifest = folder / f"{part}.json"
        manifest.write_text(
            json.dumps(
                {
                    "version": PART_VERSION,
                    "part": part,
                    "split": "train_2018_2023",
                    "final_test_accessed": False,
                    "protocol_sha256": "a" * 64,
                    "files": [
                        {
                            "path": leaf.relative_to(root).as_posix(),
                            "day": "2018-01-01",
                            "bytes": leaf.stat().st_size,
                            "sha256": file_hash(leaf),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        review["parts"][part] = {
            "status": "passed",
            "manifest_path": manifest.relative_to(root).as_posix(),
            "manifest_sha256": file_hash(manifest),
        }
    approval = {
        "decision": "approve_final_merge",
        "approved_by": "user",
        "source": "explicit_user_message",
        "review_sha256": review_digest(review),
        "approved_at_utc": "2026-10-17T00:00:00Z",
    }
    return review, approval, leaf


def test_missing_approval_rejected_before_source_access(tmp_path):
    with pytest.raises(PermissionError):
        preflight_training_merge(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_current_protocol_rejects_even_plausible_receipts(tmp_path):
    review, approval, leaf = fixture(tmp_path)
    leaf.unlink()
    with pytest.raises(PermissionError, match="Current label protocol is closed"):
        preflight_training_merge(tmp_path, review, approval)


def test_byte_verification_alone_never_merges(tmp_path):
    review, approval, _ = fixture(tmp_path)
    result = verify_final_part_files(tmp_path, review, approval)
    assert len(result["verified_files"]) == 1
    assert result["labels_created"] is result["final_merge_executed"] is False


def test_same_size_leaf_tampering_requires_new_review(tmp_path):
    review, approval, leaf = fixture(tmp_path)
    data = leaf.read_bytes()
    leaf.write_bytes(data.replace(b"1", b"0"))
    with pytest.raises(ValueError, match="Reviewed leaf bytes changed"):
        verify_final_part_files(tmp_path, review, approval)


def test_changed_manifest_rejected_even_with_unchanged_leaves(tmp_path):
    review, approval, _ = fixture(tmp_path)
    path = tmp_path / review["parts"]["targets"]["manifest_path"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Final manifest changed"):
        verify_final_part_files(tmp_path, review, approval)


@pytest.mark.parametrize("day", ["2024-01-01", "2025-01-01"])
def test_held_out_calendar_rejected_before_leaf_access(tmp_path, day):
    review, approval, leaf = fixture(tmp_path)
    path = tmp_path / review["parts"]["targets"]["manifest_path"]
    value = json.loads(path.read_text())
    value["files"][0]["day"] = day
    path.write_text(json.dumps(value))
    review["parts"]["targets"]["manifest_sha256"] = file_hash(path)
    approval["review_sha256"] = review_digest(review)
    leaf.unlink()
    with pytest.raises(ValueError, match="Training only"):
        verify_final_part_files(tmp_path, review, approval)


def test_changed_review_with_old_approval_rejected(tmp_path):
    review, approval, _ = fixture(tmp_path)
    review = copy.deepcopy(review)
    review["parts"]["weather"]["manifest_sha256"] = "b" * 64
    with pytest.raises(PermissionError):
        verify_final_part_files(tmp_path, review, approval)


@pytest.mark.parametrize("problem", ["protocol", "duplicate", "held_out_path"])
def test_inconsistent_manifest_preflight_before_leaf_read(tmp_path, problem):
    review, approval, leaf = fixture(tmp_path)
    entry = review["parts"]["targets"]
    path = tmp_path / entry["manifest_path"]
    value = json.loads(path.read_text(encoding="utf-8"))
    if problem == "protocol":
        value["protocol_sha256"] = "b" * 64
    elif problem == "duplicate":
        value["files"].append(copy.deepcopy(value["files"][0]))
    else:
        value["files"][0]["path"] = "data/interim/2025-01-01_targets.csv"
    path.write_text(json.dumps(value), encoding="utf-8")
    entry["manifest_sha256"] = file_hash(path)
    approval["review_sha256"] = review_digest(review)
    leaf.unlink()
    with pytest.raises(ValueError):
        verify_final_part_files(tmp_path, review, approval)


@pytest.mark.parametrize(
    "name",
    [
        "../outside.json",
        "C:/outside.json",
        "outputs/reports/../private.json",
        "outputs/reports/.env",
        "outputs/reports/token.json",
        "outputs\\reports\\x.json",
    ],
)
def test_private_or_escaping_paths_rejected(tmp_path, name):
    with pytest.raises(ValueError):
        public_file(tmp_path, name)
