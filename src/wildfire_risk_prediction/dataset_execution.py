"""Fail-closed execution preflight; manifest integrity is not scientific label acceptance."""

import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.final_merge_gate import PARTS, require_final_merge_approval
from wildfire_risk_prediction.target_admission import specification

PART_VERSION = "final_dataset_part_manifest_v1"


def public_file(root, name):
    """Only public, contained regular data/report files; reject parent links and private names."""
    require(isinstance(name, str) and "\\" not in name and ":" not in name, "POSIX local path")
    relative = PurePosixPath(name)
    require(
        not relative.is_absolute()
        and relative.as_posix() == name
        and all(p not in ("", ".", "..") and not p.startswith(".") for p in relative.parts)
        and name.startswith(("data/interim/", "outputs/reports/"))
        and not any(
            word in name.lower()
            for word in ("credential", "oauth", "password", "token", "drive_connection")
        ),
        "Public manifest path required",
    )
    root = Path(root).resolve()
    current = root
    for component in relative.parts:
        current = current / component
        require(
            not current.is_symlink()
            and not (hasattr(current, "is_junction") and current.is_junction()),
            "Linked source path forbidden",
        )
    require(current.resolve().is_relative_to(root) and current.is_file(), "Contained file")
    return current


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_final_part_files(root, review, approval):
    """Verify five future normalized manifests and bytes, after explicit bound review approval.

    This is a preparatory byte check. It neither generates nor scientifically validates labels.
    Future manifests must carry file dates before any leaf is opened; 2024/2025 stay sealed here.
    """
    require_final_merge_approval(review, approval)
    verified, protocols = {}, set()
    for part in PARTS:
        entry = review["parts"][part]
        manifest_path = public_file(root, entry.get("manifest_path"))
        require(file_hash(manifest_path) == entry["manifest_sha256"], "Final manifest changed")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        require(
            manifest.get("version") == PART_VERSION
            and manifest.get("part") == part
            and manifest.get("split") == "train_2018_2023"
            and manifest.get("final_test_accessed") is False
            and isinstance(manifest.get("files"), list)
            and bool(manifest["files"]),
            "Final part manifest schema/scope",
        )
        protocol = manifest.get("protocol_sha256")
        require(
            isinstance(protocol, str) and re.fullmatch(r"[0-9a-f]{64}", protocol),
            "Protocol identity",
        )
        protocols.add(protocol)
        require(len(protocols) == 1, "All parts need the same scientific protocol")
        names = set()
        for record in manifest["files"]:
            training_day(record["day"])  # Before opening any leaf, including a held-out source.
            name, expected = record["path"], record["sha256"]
            require(
                isinstance(name, str) and not re.search(r"(?:^|[/_\-])202[45](?:$|[/_.\-])", name),
                "Held-out leaf path forbidden even with a training date declaration",
            )
            require(name not in names, "Duplicate part file")
            names.add(name)
            require(
                isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "Leaf digest"
            )
            require(type(record["bytes"]) is int and record["bytes"] > 0, "Positive leaf size")
    # Complete schema/date preflight of all five manifests precedes every CSV byte read.
    for part in PARTS:
        entry = review["parts"][part]
        manifest_path = public_file(root, entry["manifest_path"])
        require(file_hash(manifest_path) == entry["manifest_sha256"], "Final manifest changed")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for record in manifest["files"]:
            path = public_file(root, record["path"])
            require(
                path.stat().st_size == record["bytes"] and file_hash(path) == record["sha256"],
                "Reviewed leaf bytes changed; new final review and approval required",
            )
            require(
                record["path"] not in verified or verified[record["path"]] == record["sha256"],
                "Conflicting shared leaf identity",
            )
            verified[record["path"]] = record["sha256"]
    for part in PARTS:
        entry = review["parts"][part]
        require(
            file_hash(public_file(root, entry["manifest_path"])) == entry["manifest_sha256"],
            "Final manifest changed during verification",
        )
    return {
        "status": "reviewed_part_bytes_verified_only",
        "verified_files": verified,
        "labels_created": False,
        "final_merge_executed": False,
    }


def preflight_training_merge(root, review=None, approval=None):
    """A plausible receipt or caller boolean cannot open the current scientific protocol.

    The current v1 has no accepted binary label builder. A new evidence-based protocol and
    corresponding implementation will be needed after scientific decisions, not a flag toggle.
    """
    require_final_merge_approval(review, approval)
    state = specification()
    if not (state["positive_label_permitted"] and state["negative_label_permitted"]):
        raise PermissionError("Current label protocol is closed; accepted new builder required")
    return verify_final_part_files(root, review, approval)
