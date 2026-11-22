"""Quality review of the one delivered FWI pilot; no time binding, model or label production."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import inspect_fwi_reference_metadata as header
import numpy as np
import pandas as pd
import rasterio

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/fwi_delivery_quality_review_v1.json"
FILE = ROOT / "data/raw/external/cems_fwi_pilot_v1/ff72cf1a14e9faea5681118fe8888717.nc"
HEADER = BASE / "fwi_reference_metadata_v1/20261122T164628Z_846e19fc/readback.json"


def quality(values):
    """Preserve all values; zero is valid, and FWI is not capped at 100."""
    masked = np.ma.asarray(values)
    raw = np.asarray(masked.data)
    declared = np.ma.getmaskarray(masked)
    finite = ~declared & np.isfinite(raw)
    x = raw[finite].astype(float)
    require(len(x) > 0, "Some finite unmasked FWI support is required")
    return {
        "points": raw.size,
        "declared_missing": int(declared.sum()),
        "unmasked_nonfinite": int((~declared & ~np.isfinite(raw)).sum()),
        "finite": len(x),
        "negative": int((x < 0).sum()),
        "zero_valid": int((x == 0).sum()),
        "above_100_not_automatically_invalid": int((x > 100).sum()),
        "minimum": float(x.min()),
        "median": float(np.median(x)),
        "maximum": float(x.max()),
    }


def main():
    decision = json.loads(CONFIG.read_bytes())
    require(
        decision["scope"] == "one_received_June_2022_FWI_file_quality_only"
        and decision["local_value_quality_read_authorized"] is True
        and all(
            decision[k] is False
            for k in (
                "new_2023_2024_2025_values_permitted",
                "automatic_T_minus_one_feature_admission",
                "operational_availability_verified",
                "new_model_or_labels_permitted",
                "risk_band_or_probability_permitted",
                "final_merge_permitted",
            )
        ),
        "Bounded received-file quality scope",
    )
    require(
        digest(FILE) == decision["source_file_sha256"]
        and digest(HEADER) == decision["header_readback_sha256"],
        "Exact original bytes and completed header receipt",
    )
    initial = json.loads(HEADER.read_bytes())
    require(
        FILE.stat().st_size == initial["input_bytes"] <= 32 * 1024 * 1024,
        "Small original pilot unchanged",
    )
    pins = {
        FILE: digest(FILE),
        HEADER: digest(HEADER),
        CONFIG: digest(CONFIG),
        Path(header.__file__): digest(Path(header.__file__)),
    }
    rows = []
    with rasterio.open(FILE) as dataset:
        tags = dataset.tags()
        require(
            dataset.driver == "netCDF"
            and (dataset.count, dataset.height, dataset.width) == (30, 21, 49),
            "Exact monthly regional shape",
        )
        require(
            dataset.tags(1).get("NETCDF_VARNAME") == "fwinx"
            and tags.get("fwinx#GRIB_shortName") == "fwinx"
            and tags.get("fwinx#GRIB_paramId") == "260540",
            "Delivered FWI variable identity",
        )
        require(
            tags.get("longitude#units") == "degrees_east"
            and tags.get("latitude#units") == "degrees_north"
            and tags.get("fwinx#GRIB_gridType") == "regular_ll",
            "Explicit CF/GRIB geographic-axis metadata",
        )
        require(
            dataset.xy(0, 0) == (25.0, 40.0)
            and dataset.xy(20, 48) == (37.0, 35.0)
            and dataset.res == (0.25, 0.25),
            "Requested grid-node bounds and spacing",
        )
        expected_times = [
            (datetime(2022, 6, 1, tzinfo=UTC) + timedelta(days=i)).isoformat() for i in range(30)
        ]
        require(
            initial["metadata"]["nominal_CF_times"] == expected_times,
            "One nominal date for each June day",
        )
        require(
            all(s == 1 for s in dataset.scales) and all(o == 0 for o in dataset.offsets),
            "Known native scale and offset",
        )
        for band, stamp in enumerate(expected_times, start=1):
            epoch = float(dataset.tags(band)["NETCDF_DIM_valid_time"])
            require(
                datetime.fromtimestamp(epoch, tz=UTC).isoformat() == stamp,
                "Independent per-band nominal time",
            )
            values = dataset.read(band, masked=True)
            rows.append({"nominal_timestamp_utc_not_availability": stamp, **quality(values)})
        meta = {
            k: v
            for k, v in tags.items()
            if k.startswith(("fwinx#", "valid_time#", "latitude#", "longitude#"))
        }
        source_crs = str(dataset.crs)
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Source file and prior header remain unchanged",
    )
    out = (
        BASE
        / "fwi_received_quality_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(out / "daily_native_grid_quality.csv", index=False)
    report = {
        "status": "received_FWI_native_file_quality_reviewed_not_feature_or_time_policy_admission",
        "decision": decision,
        "days": 30,
        "native_points_per_day": 1029,
        "total_points": sum(r["points"] for r in rows),
        "finite_points": sum(r["finite"] for r in rows),
        "declared_missing_points": sum(r["declared_missing"] for r in rows),
        "unmasked_nonfinite_points": sum(r["unmasked_nonfinite"] for r in rows),
        "negative_points": sum(r["negative"] for r in rows),
        "zero_points_valid": sum(r["zero_valid"] for r in rows),
        "above_100_not_automatically_invalid": sum(
            r["above_100_not_automatically_invalid"] for r in rows
        ),
        "minimum": min(r["minimum"] for r in rows),
        "maximum": max(r["maximum"] for r in rows),
        "source_CRS_property": source_crs,
        "geographic_coordinates_verified_by_CF_GRIB_axes": True,
        "CRS_assigned_or_file_reprojected": False,
        "native_resolution_is_5km": False,
        "preserved_variable_metadata": meta,
        "nominal_midnight_is_observation_or_publication_time": False,
        "new_model_features_or_labels_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {
            "daily_native_grid_quality.csv": digest(out / "daily_native_grid_quality.csv")
        },
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(
        "finite",
        report["finite_points"],
        "declared missing",
        report["declared_missing_points"],
        "negative",
        report["negative_points"],
        "range",
        report["minimum"],
        report["maximum"],
        flush=True,
    )


if __name__ == "__main__":
    main()
