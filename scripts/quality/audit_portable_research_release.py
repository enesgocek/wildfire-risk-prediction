"""Audit separate scientific parts and exercise a relocated extracted interface."""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from verify_local_research_release import verify

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.portable_review_links import local_target, verify_html

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PREVIOUS = BASE / "local_research_release_v2/20261124T023339Z_6f277b31"
UI = BASE / "historical_research_prototype_v3/20261124T173653Z_3a064f3e"


def check(condition, message):
    if not condition:
        raise ValueError(message)


def context(path):
    raw = path.read_text(encoding="utf-8").strip()
    prefix = "globalThis.RESEARCH_CONTEXT="
    check(raw.startswith(prefix) and raw.endswith(";"), "Static context assignment")
    return json.loads(raw[len(prefix) : -1])


def main(release):
    container = verify(release)
    package = release / "package"
    manifest = json.loads((package / "manifest.json").read_bytes())
    check(
        manifest["experimental_research_only"]
        and not manifest["labelled_training_dataset"]
        and not manifest["final_merge"],
        "Experimental separate-part delivery",
    )
    old_manifest = json.loads((PREVIOUS / "package/manifest.json").read_bytes())
    unchanged = 0
    for name, entry in old_manifest["files"].items():
        if name.startswith("interface/") or name in ("README.md", "AI_USE.md"):
            continue
        check(
            manifest["files"][name]["sha256"] == entry["sha256"],
            "Unchanged existing release member",
        )
        unchanged += 1
    for name in (
        "inceleme.html",
        "research-app.js",
        "research-core.js",
        "research-map.js",
        "review_data.js",
        "geography_data.js",
    ):
        check(digest(package / "interface" / name) == digest(UI / name), "Current UI byte copy")
    original = context(UI / "research_context.js")
    relocated = context(package / "interface/research_context.js")
    check(set(original) == set(relocated), "Same context schema")
    check(
        all(original[k] == relocated[k] for k in original if k != "links"),
        "Only link paths changed",
    )
    check(
        [(r["label"], r["sha256"]) for r in original["links"]]
        == [(r["label"], r["sha256"]) for r in relocated["links"]],
        "Same evidence contents",
    )
    html_links = verify_html(package, "index.html") + verify_html(
        package, "interface/inceleme.html"
    )
    for link in relocated["links"]:
        target = local_target(package, "interface/inceleme.html", link["path"])
        check(digest(target) == link["sha256"], "Portable evidence target bytes")
    keys, cells, complete, rows = set(), set(), 0, 0
    with (package / "data/features.csv").open(encoding="utf-8", newline="") as stream:
        data = csv.DictReader(stream)
        check(len(data.fieldnames) == 29, "27 existing feature fields")
        fields = data.fieldnames[2:]
        for row in data:
            key = row["grid_id"], row["prediction_timestamp_utc"]
            check(
                key not in keys and 2018 <= int(key[1][:4]) <= 2022, "Unique approved feature years"
            )
            keys.add(key)
            cells.add(key[0])
            complete += int(all(row[f] not in ("", "nan", "NaN") for f in fields))
            rows += 1
    check((rows, len(cells), complete) == (44082, 822, 41358), "Feature cardinality preserved")
    with (package / "data/inspection_memberships.csv").open(encoding="utf-8", newline="") as stream:
        memberships = list(csv.DictReader(stream))
    check(
        {(r["grid_id"], r["prediction_timestamp_utc"]) for r in memberships} == keys
        and len(memberships) == len(keys),
        "Separate memberships retain identical keys",
    )
    check(
        all(
            r["target"] == r["accepted_L_membership"] == ""
            and r["daily_observation_status"] == "unknown"
            and r["negative_label_permitted"].lower() == "false"
            for r in memberships
        ),
        "No new true targets or negatives",
    )
    check(
        len(list((package / "models").glob("*/ranker.json"))) == 9,
        "Nine original models, no new model",
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "portable_release_relocation_audit_v1" / stamp
    extracted = out / "extracted"
    check(
        extracted.resolve().is_relative_to((ROOT / "outputs").resolve()),
        "Owned isolated extraction directory",
    )
    extracted.mkdir(parents=True, exist_ok=False)
    # The archive member inventory/hash/CRC has passed before extracting any member.
    with zipfile.ZipFile(release / "research_release.zip") as archive:
        archive.extractall(extracted)
    for name, entry in manifest["files"].items():
        check(digest(extracted / name) == entry["sha256"], "Extracted member bytes")
    verify_html(extracted, "index.html")
    verify_html(extracted, "interface/inceleme.html")
    for link in context(extracted / "interface/research_context.js")["links"]:
        target = local_target(extracted, "interface/inceleme.html", link["path"])
        check(digest(target) == link["sha256"], "Relocated evidence bytes")
    node = shutil.which("node")
    check(node is not None, "Existing local DOM test runtime")
    test = ROOT / "tests/js/research_prototype_v3_dom.test.cjs"
    result = subprocess.run(
        [node, "--test", "--test-reporter=tap", str(test)],
        cwd=ROOT,
        env=os.environ | {"RESEARCH_PROTOTYPE_DIR": str(extracted / "interface")},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    (out / "relocated_dom_interactions.tap").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    check(
        result.returncode == 0
        and re.search(r"# tests 14\b", result.stdout)
        and re.search(r"# pass 14\b", result.stdout),
        "Fourteen relocated offline interaction tests",
    )
    body = {
        "status": "portable_release_bytes_scientific_scope_links_and_relocated_DOM_verified",
        "release_path": release.relative_to(ROOT).as_posix(),
        "container": container,
        "unchanged_base_members": unchanged,
        "feature_rows": rows,
        "feature_cells": len(cells),
        "complete_27_feature_rows": complete,
        "html_references_verified": html_links,
        "portable_evidence_targets": len(relocated["links"]),
        "relocated_DOM_tests_passed": 14,
        "extracted_path": extracted.relative_to(ROOT).as_posix(),
        "actual_browser_visual_render_verified": False,
        "new_training_or_labels": False,
        "final_merge": False,
        "release_readback_sha256": digest(release / "readback.json"),
        "manifest_sha256": digest(package / "manifest.json"),
        "zip_sha256": digest(release / "research_release.zip"),
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    main(parser.parse_args().release.resolve())
