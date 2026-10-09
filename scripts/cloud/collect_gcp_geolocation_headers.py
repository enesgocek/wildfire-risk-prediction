"""Read only public pairing header fields from retained local NetCDF files.

No login, download, arrays, production writes or resource control. Exports a
new small ZIP. A pinned prior diagnostic supplies scope and package validation.
"""

import ast
import contextlib
import hashlib
import importlib.util
import json
import os
import re
import sys
import warnings
import zipfile
from pathlib import Path

PROBE_SHA = "2ae1c48c87ce69701189319fb0c981fc1839bd8d263c303bdaecaa5d5d22a787"
GEO = re.compile(r"(?:VNP03IMG|VJ103IMG)\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc")


def require(ok, label):
    if not ok:
        raise ValueError(label)


def safe_reference(value, selected):
    require(isinstance(value, str) and len(value) <= 8192, "Header reference bound")
    names = GEO.findall(value)
    return {
        "geolocation_filenames": sorted(set(names)),
        "literal_matches_selected": value == selected,
        "value_sha256": hashlib.sha256(value.encode()).hexdigest(),
        "nonstandard_format": not bool(GEO.fullmatch(value)),
    }


def header_row(pair, fire_tags, geo_tags):
    fire = next(s["filename"] for s in pair["sources"] if s["role"] == "fire")
    selected = next(s["filename"] for s in pair["sources"] if s["role"] == "geolocation")
    return {
        "sample_id": pair["sample_id"],
        "fire_filename": fire,
        "selected_geolocation_filename": selected,
        "declared_fields": {
            key: safe_reference(fire_tags[key], selected)
            for key in ("VNP03IMG", "VJ103IMG")
            if key in fire_tags
        },
        "input_pointer": safe_reference(fire_tags.get("InputPointer", ""), selected),
        "selected_geo_local_id_matches": geo_tags.get("LocalGranuleID") == selected,
        "fire_short_name_matches": fire_tags.get("ShortName") == fire.split(".")[0],
        "geolocation_short_name_matches": geo_tags.get("ShortName") == selected.split(".")[0],
    }


def guard_labels(path):
    labels = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "require"
            and len(node.args) > 1
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            labels.add(node.args[1].value)
    return labels


def main():
    home = Path.home()
    path = home / "probe_gcp_retained_sources.py"
    require(
        not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == PROBE_SHA,
        "Pinned probe helper",
    )
    spec = importlib.util.spec_from_file_location("checked_probe", path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    capture = probe.helper(home)
    original = home / "wildfire-gcp-production-package"
    controller = home / "wildfire-gcp-acceleration-package"
    work = home / "wildfire-gcp-production-v1"
    target = home / "gcp_geolocation_headers_2026-10-09.zip"
    require(not target.exists() and not target.is_symlink(), "Header report already exists")
    probe.block_network()
    with capture.lock(work):
        capture.pinned(original, "production_manifest.json", capture.SCOPE)
        capture.pinned(controller, "acceleration_manifest.json", capture.CONTROLLER)
        state = capture.state(capture.read(work / "progress.json", work, 65536))
        month = work / "months" / state["failed_month"]
        data = capture.read(month / "metadata/month.json", work, 2_000_000)
        require(
            state["failed_month"] == "2023-12"
            and hashlib.sha256(data).hexdigest() == probe.MONTH_SHA,
            "Pinned month plan",
        )
        plan = json.loads(data)
        pairs = {hashlib.sha256(p["sample_id"].encode()).hexdigest(): p for p in plan["pairs"]}
        roots = sorted((month / "accelerated_run/tasks").iterdir())
        require(
            0 < len(roots) <= 100
            and all(r.is_dir() and not r.is_symlink() and r.name in pairs for r in roots),
            "Retained header task boundary",
        )
        sys.path.insert(0, str(original))
        import rasterio
        import run_gcp_production as runner

        _, native = runner.science(roots[0])
        audit = native.audit
        labels = guard_labels(Path(audit.__file__))
        rows = []
        for root in roots:
            pair = pairs[root.name]
            raw = root / "summer/raw" / pair["stem"]
            paths = {s["role"]: raw / s["filename"] for s in pair["sources"]}
            before = {}
            for source in pair["sources"]:
                p = paths[source["role"]]
                require(
                    not p.is_symlink()
                    and p.resolve().is_relative_to(root.resolve())
                    and p.is_file()
                    and p.stat().st_size == source["bytes"],
                    "Header raw boundary/size",
                )
                before[p] = (p.stat().st_size, p.stat().st_mtime_ns)
            with warnings.catch_warnings(), contextlib.ExitStack() as stack:
                warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
                fire_tags = audit.layer(stack, paths["fire"], "fire_mask").tags()
                geo_tags = audit.layer(
                    stack, paths["geolocation"], "geolocation_data/latitude"
                ).tags()
                row = header_row(pair, fire_tags, geo_tags)
                try:
                    audit.validate_pair(paths["fire"], paths["geolocation"], fire_tags, geo_tags)
                    row["frozen_header_check"] = "passed"
                except Exception as error:
                    row["frozen_header_check"] = "failed"
                    row["error_type"] = type(error).__name__
                    row["guard"] = str(error) if str(error) in labels else "CLASS_ONLY"
            require(
                all((p.stat().st_size, p.stat().st_mtime_ns) == stat for p, stat in before.items()),
                "Raw file changed during header read",
            )
            rows.append(row)
        report = {
            "protocol": "gcp_geolocation_header_capture_v1",
            "rows": rows,
            "diagnostic_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "probe_sha256": PROBE_SHA,
            "month_plan_sha256": probe.MONTH_SHA,
            "original_manifest_sha256": capture.SCOPE,
            "controller_manifest_sha256": capture.CONTROLLER,
            "network_requests": 0,
            "raw_downloads": 0,
            "pixel_arrays_read": False,
            "credentials_read": False,
            "production_writes": 0,
            "limitation": "Header capture only; no new native scientific acceptance",
        }
        encoded = json.dumps(report, sort_keys=True).encode()
        require(len(encoded) < 1_000_000, "Header export bound")
        with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("header_report.json", encoded)
    print("HEADER REPORT COMPLETE", len(rows), "pairs")
    print("Download:", target)
    print("Stop VM after downloading; no production was started.")


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        print("Header collection failed:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
