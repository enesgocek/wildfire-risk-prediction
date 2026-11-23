"""Bounded PDT 4.93 clock review and one-band format comparison; no model input admission."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np
import rasterio

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
GRIB = ROOT / "data/raw/external/cems_fwi_pilot_v1/963fa09b86438339fee3886631262c59.grib"
NETCDF = ROOT / "data/raw/external/cems_fwi_pilot_v1/ff72cf1a14e9faea5681118fe8888717.nc"
HEADER = BASE / "fwi_grib_metadata_v1/20261123T001516Z_7c2202c2/readback.json"
SOURCES = BASE / "fwi_grib_definition_sources_v1/20261123T001639Z_61612b3f"


def sections(message):
    require(
        20 <= len(message) <= 32 * 1024 * 1024
        and message[:4] == b"GRIB"
        and message[7] == 2
        and int.from_bytes(message[8:16], "big") == len(message)
        and message[-4:] == b"7777",
        "One intact bounded GRIB2 message",
    )
    result = {}
    pos = 16
    while pos < len(message) - 4:
        require(pos + 5 <= len(message) - 4, "Complete section header")
        size = int.from_bytes(message[pos : pos + 4], "big")
        kind = message[pos + 4]
        require(size >= 5 and pos + size <= len(message) - 4, "Complete section length")
        require(kind in range(1, 8) and kind not in result, "One field without repeated sections")
        result[kind] = message[pos : pos + size]
        pos += size
    require(pos == len(message) - 4 and {1, 3, 4, 5, 6, 7} <= result.keys(), "Complete field")
    return result


def stamp(raw, offset):
    return datetime(int.from_bytes(raw[offset : offset + 2], "big"), *raw[offset + 2 : offset + 7])


def local_clock(message):
    """Only exact deterministic, surface, one-forcing-record 4.93 is supported."""
    parts = sections(message)
    s1, s4 = parts[1], parts[4]
    require(len(s1) == 21 and s1[11] == 4, "Reference is local time, not a UTC issue time")
    require(
        len(s4) == 51
        and int.from_bytes(s4[5:7], "big") == 0
        and int.from_bytes(s4[7:9], "big") == 93,
        "Exact one-record PDT 4.93 layout",
    )
    require(message[6] == 2 and s4[9:11] == bytes([4, 5]), "Land/fire/FWI parameter")
    require(s4[19] == 1 and s4[25] == 255, "Single surface")
    require(s4[31] == 1 and s4[32] == 1, "Interpolated local time, one forcing record")
    require(s4[40] == 1 and s4[46] == 1, "Explicit hourly forcing units")
    base = stamp(s4, 33).replace(tzinfo=UTC)
    first = int.from_bytes(s4[41:45], "big")
    count = s4[45]
    increment = int.from_bytes(s4[47:51], "big")
    require(1 <= count <= 24 and 0 < increment <= 24 and first <= 48, "Bounded forcing steps")
    times = [base + timedelta(hours=first + i * increment) for i in range(count)]
    return {
        "product_definition_template": 93,
        "reference_time_significance_code": 4,
        "reference_time_meaning": "local_time_not_UTC_issue_time",
        "local_reference_wall_clock_without_timezone": stamp(s1, 12).isoformat(),
        "local_time_method": 1,
        "local_time_method_meaning": "interpolated_at_specified_local_time",
        "forcing_base_UTC": base.isoformat(),
        "first_step_hours": first,
        "number_of_steps": count,
        "step_increment_hours": increment,
        "forcing_timestamps_UTC": [t.isoformat() for t in times],
        "forcing_last_UTC": times[-1].isoformat(),
        "publication_or_acquisition_timestamp": None,
    }


def compare_arrays(left, right, tolerance):
    a, b = np.ma.asarray(left), np.ma.asarray(right)
    require(a.shape == b.shape, "Same native array shape")
    require(np.array_equal(np.ma.getmaskarray(a), np.ma.getmaskarray(b)), "Same missing mask")
    x, y = a.compressed().astype(float), b.compressed().astype(float)
    require(len(x) > 0 and np.isfinite(x).all() and np.isfinite(y).all(), "Finite shared support")
    delta = np.abs(x - y)
    require(float(delta.max()) <= tolerance, "Values within packing-based tolerance")
    return {
        "finite_points_compared": len(x),
        "missing_points_each": int(np.ma.getmaskarray(a).sum()),
        "same_mask": True,
        "max_absolute_difference": float(delta.max()),
        "mean_absolute_difference": float(delta.mean()),
        "exact_equal_finite_points": int((x == y).sum()),
        "comparison_tolerance": float(tolerance),
    }


def main():
    expected = {
        GRIB: "f98b51cfb5cff1fbfe4bcd37b5160a97248d639a88624b73f7eae8975815245f",
        NETCDF: "e6b57e8ecbd5836f141eb6d0cbd17dc283d6569bb194c5496861d4ba8e5f5a8e",
        HEADER: "90a4b8c054f34eb3bc6140b5e3a6a930dd2e4b3bba6a487b322a2008c6cf7d1c",
        SOURCES
        / "readback.json": "ed4014d5fd2e81c3e309ed6c6470cafef4b64a97fc0bc758123633b89ae0aabe",
        SOURCES / "additional_definitions.json": (
            "c8c30e9e1d6786cd4fcd4a5f34a76d963a11444d12b69c97d42e648b1bf8e82b"
        ),
    }
    for p, sha in list(expected.items()):
        require(digest(p) == sha, "Pinned original or definition receipt")
    for name in ("readback.json", "additional_definitions.json"):
        for row in json.loads((SOURCES / name).read_bytes())["files"]:
            p = SOURCES / row["file"]
            require(digest(p) == row["sha256"], "Unchanged official source definition")
            expected[p] = row["sha256"]
    raw = GRIB.read_bytes()
    clock = local_clock(raw)
    require(
        clock["local_reference_wall_clock_without_timezone"] == "2022-06-01T12:00:00", "Pilot day"
    )
    # Section 5, DRT 5.0: derive the native quantization rather than choose a fitted threshold.
    s5 = sections(raw)[5]
    require(len(s5) == 21 and s5[9:11] == b"\x00\x00", "Simple packing DRT 5.0")

    def signed_magnitude(x):
        return -(x & 32767) if x & 32768 else x

    binary = signed_magnitude(int.from_bytes(s5[15:17], "big"))
    decimal = signed_magnitude(int.from_bytes(s5[17:19], "big"))
    quantum = 2.0**binary * 10.0 ** (-decimal)
    with rasterio.open(GRIB) as g, rasterio.open(NETCDF) as n:
        require(
            g.count == 1
            and n.count == 30
            and g.shape == n.shape == (21, 49)
            and g.transform == n.transform,
            "Same native pilot grid; no resampling",
        )
        require(
            n.tags(1).get("NETCDF_DIM_valid_time") == "1654041600", "NetCDF June 1 nominal band"
        )
        left, right = g.read(1, masked=True), n.read(1, masked=True)
        tolerance = quantum + 2 * np.finfo(np.float32).eps * max(1, float(abs(right).max()))
        comparison = compare_arrays(left, right, tolerance)
    require(all(digest(p) == h for p, h in expected.items()), "All original inputs unchanged")
    out = (
        BASE
        / "fwi_local_time_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    result = {
        "status": "one_day_clock_and_format_equivalence_reviewed_not_model_admission",
        "clock": clock,
        "one_day_format_comparison": comparison,
        "native_packing_quantum": quantum,
        "CRS_equivalence_verified": False,
        "projection_or_resampling_performed": False,
        "GDAL_GENERIC_VALID_TIME_zero_rejected": True,
        "same_day_nominal_midnight_availability_verified": False,
        "all_month_GRIB_forcing_metadata_verified": False,
        "prior_day_reference_direction": "proposal_only_retrospective_not_operational_availability",
        "actual_operational_latency_verified": False,
        "new_X_models_labels_risk_colors_or_final_merge": 0,
        "closed_year_values_opened": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in expected.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    target = out / "readback.json"
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(target), flush=True)
    print(json.dumps({"clock": clock, "comparison": comparison}, indent=2), flush=True)


if __name__ == "__main__":
    main()
