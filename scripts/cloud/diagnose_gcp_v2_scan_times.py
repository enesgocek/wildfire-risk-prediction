"""Read-only single-source scan replay; no login, downloads or production writes."""

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

HELPER_SHA = "f4d9d13494f552fe178d19041cd0b2e3d5c0d2c0be08f6440aa9464de35cee83"
PLAN_SHA = "a9cb1870893754acd663a307ef14a49523831603d6649467c09ae204fc786e03"
FOCUS = "SNPP:2022252.2230"
STEM = "l2_sample_2022252.2230"
UTC_ISO = r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|\+00:00)"


class ProbeCheck(ValueError):
    """Printable constant checks belong to this diagnostic only."""


def require(ok, label):
    if not ok:
        raise ProbeCheck(label)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def helper(home):
    path = home / "collect_gcp_v2_failure_snapshot.py"
    require(
        path.is_file() and not path.is_symlink() and digest(path) == HELPER_SHA,
        "Pinned snapshot helper",
    )
    spec = importlib.util.spec_from_file_location("checked_v2_snapshot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def no_network():
    def audit(event, _args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.bind"}:
            raise ProbeCheck("Diagnostic network forbidden")

    sys.addaudithook(audit)


def parse_times(frame, native):
    """Compare frozen default parsing with explicit ISO; both must preserve native ns."""
    import numpy as np
    import pandas as pd

    rows = []
    for name, actual in native.items():
        values = frame[name]
        require(
            values.notna().all() and values.astype(str).str.fullmatch(UTC_ISO).all(),
            "Reference UTC schema",
        )
        row = {
            "column": name,
            "rows": len(values),
            "fractional_rows": int(values.astype(str).str.contains(r"\.\d+").sum()),
        }
        try:
            parsed = pd.to_datetime(values, utc=True, errors="raise")
            row["default_status"] = "passed"
            row["default_exact_native_ns"] = bool(np.array_equal(parsed.array.asi8, actual.asi8))
        except ValueError:
            row["default_status"] = "ValueError"
            row["default_exact_native_ns"] = None
        explicit = pd.to_datetime(values, utc=True, errors="raise", format="ISO8601")
        row["iso_exact_native_ns"] = bool(np.array_equal(explicit.array.asi8, actual.asi8))
        require(row["iso_exact_native_ns"], "ISO parser changes native time")
        rows.append(row)
    return rows


def error_location(error, root, files, labels, snapshot):
    """Keep only checked science file/function/line, never traceback text or locals."""
    message = error.args[0] if len(error.args) == 1 else None
    frames = []
    tb = error.__traceback__
    while tb:
        path = Path(tb.tb_frame.f_code.co_filename).resolve()
        if path.is_relative_to(root.resolve()):
            name = path.relative_to(root.resolve()).as_posix()
            function = tb.tb_frame.f_code.co_name
            if name in files and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,80}", function):
                frames.append({"file": name, "line": tb.tb_lineno, "function": function})
        tb = tb.tb_next
    return {
        "error_type": snapshot.safe_error(type(error).__name__),
        "guard": message if isinstance(message, str) and message in labels else "CLASS_ONLY",
        "scientific_frames": frames[-6:],
    }


def run(home, snapshot):
    import geopandas as gpd
    import pandas as pd
    import shapely
    from pyproj import Transformer

    saved = snapshot.collect(home)
    require(
        saved["focus_sample"] == FOCUS and saved["month_plan_sha256"] == PLAN_SHA,
        "Focus snapshot identity",
    )
    require(
        all(
            s["present"] and s["actual_bytes"] == s["expected_bytes"]
            for s in saved["focus_raw_inventory"]
        ),
        "Retained raw sizes",
    )
    work = home / "wildfire-gcp-production-v1"
    plan_path = work / "months/2022-09/metadata/month.json"
    require(digest(plan_path) == PLAN_SHA, "Pinned September plan")
    pair = next(p for p in json.loads(plan_path.read_bytes())["pairs"] if p["sample_id"] == FOCUS)
    root = work / "months/2022-09/accelerated_run/tasks" / snapshot.sha(FOCUS.encode())
    snapshot.boundary(root, work)
    sys.path.insert(0, str(home / "wildfire-gcp-production-package"))
    import run_gcp_production as runner

    _, native = runner.science(root)  # Hash-checks every frozen science member before loading.
    output = root / "summer/results"
    for module in (native, native.area, native.area.audit, native.audit, native.timing):
        module.OUTPUT = output
    source_manifest = json.loads((root / "summer/manifest.json").read_bytes())
    files = set(source_manifest["bundle_files"]) | {"scripts/cloud/l2_daily_compact.py"}
    labels = set()
    for name in files:
        if name.endswith(".py"):
            labels.update(snapshot.guards(snapshot.read(root / name, root)))
    paths = [plan_path, work / "progress.json"]
    paths.extend(root / "summer/raw" / STEM / s["filename"] for s in pair["sources"])
    paths.extend(
        output / (STEM + "_" + suffix)
        for suffix in snapshot.NATIVE_SUFFIXES
        if (output / (STEM + "_" + suffix)).is_file()
    )
    for path in paths:
        snapshot.boundary(path, work)
    before = {path: digest(path) for path in paths}
    report = {
        "protocol": "gcp_v2_single_scan_replay_v1",
        "focus_sample": FOCUS,
        "month_plan_sha256": PLAN_SHA,
        "helper_sha256": HELPER_SHA,
        "probe_sha256": digest(Path(__file__).resolve()),
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "credentials_read": False,
        "raw_downloads": 0,
        "production_writes": 0,
        "native_code_changed": False,
        "historical_exception_automatically_proven": False,
        "limits": "One read-only scan replay; no new scientific output or queue acceptance",
    }
    try:
        reference = pd.read_csv(output / (STEM + "_scan_times.csv"))
        geo = next(s for s in pair["sources"] if s["role"] == "geolocation")
        geo_path = root / "summer/raw" / STEM / geo["filename"]
        with contextlib.ExitStack() as stack:
            lat = native.audit.layer(stack, geo_path, "geolocation_data/latitude")
            offset = int(lat.tags()["TAI93_leapseconds"])
            values = {}
            for name, band in (
                ("start_utc", "scan_start_time"),
                ("end_utc", "scan_end_time"),
                ("ev_mid_utc", "ev_mid_time"),
            ):
                raw = (
                    native.audit.layer(stack, geo_path, "scan_line_attributes/" + band)
                    .read(1)
                    .ravel()
                )
                values[name] = native.area.tai93_utc(raw, offset)
        report["parser_comparison"] = parse_times(reference, values)
        parts_path, parts = native.area.load_parts()
        aoi = gpd.read_file(root / "data/aoi/aoi.geojson").to_crs(4326).geometry.union_all()
        shapely.prepare(aoi)
        try:
            centers, scans, provenance, _ = native.timing.source_scans(
                pair["sensor"],
                pair["key"],
                aoi,
                Transformer.from_crs(4326, 6933, always_xy=True),
                set(parts.grid_id),
            )
            report["scan_replay"] = {
                "status": "passed",
                "center_rows": len(centers),
                "scan_rows": len(scans),
                "native_counts_match": provenance["native_grid_counts_exact_match"],
            }
        except Exception as error:
            report["scan_replay"] = {
                "status": "local_failure_reproduced",
                **error_location(error, root, files, labels, snapshot),
            }
    except Exception as error:
        report["preparation_error"] = error_location(error, root, files, labels, snapshot)
    require(
        all(path.is_file() and digest(path) == value for path, value in before.items()),
        "Production input changed during probe",
    )
    report["production_input_hashes_unchanged"] = True
    report["input_hashes"] = {
        "month_plan": before[plan_path],
        **{p.name: value for p, value in before.items() if p != plan_path},
    }
    return report


def main():
    require(
        sys.platform == "linux"
        and sys.version_info[:2] == (3, 12)
        and sys.prefix != sys.base_prefix,
        "Existing Linux Python environment",
    )
    home = Path.home()
    snapshot = helper(home)
    no_network()
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (6 * 2**30, 6 * 2**30))
    with snapshot.stopped_lock(home / "wildfire-gcp-production-v1"):
        # GDAL may warn about source georeferencing; neither stderr nor external text is exported.
        with (
            open(os.devnull, "w") as quiet,
            contextlib.redirect_stdout(quiet),
            contextlib.redirect_stderr(quiet),
        ):
            report = run(home, snapshot)
        report["created_at_utc"] = datetime.now(UTC).isoformat()
        data = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode()
        require(len(data) < 100000, "Probe output byte bound")
        target = home / (
            "gcp_v2_scan_time_probe_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        )
        with target.open("xb") as stream:
            stream.write(data)
    print("Single-source read-only scan check completed")
    print("Download:", target)
    print("Stop VM after downloading; production was not resumed")


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    os.umask(0o077)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "GDAL_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    try:
        main()
    except ProbeCheck as error:
        print("Scan probe check failed:", str(error))
        raise SystemExit(1) from None
    except Exception as error:
        print("Scan probe stopped:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
