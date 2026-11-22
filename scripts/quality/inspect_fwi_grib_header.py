"""Inspect companion GRIB metadata only; no FWI values, time-policy adoption or feature binding."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import rasterio

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/external/cems_fwi_pilot_v1"


def check_file(path, raw_root):
    path = path.resolve()
    require(path.is_relative_to(raw_root.resolve()) and path.is_file(), "Local companion file only")
    require(path.suffix.lower() in {".grib", ".grb", ".grib2", ".grb2"}, "Explicit GRIB companion")
    require(8 < path.stat().st_size <= 32 * 1024 * 1024, "Bounded pilot file")
    with path.open("rb") as stream:
        header = stream.read(8)
    require(header[:4] == b"GRIB" and header[7] in (1, 2), "GRIB signature and edition, not HTML")
    return path, header[7]


def main(path):
    path, edition = check_file(path, RAW)
    original_sha = digest(path)
    with rasterio.open(path) as source:
        require(
            source.driver == "GRIB"
            and source.count <= 31
            and source.width <= 100
            and source.height <= 100,
            "Small companion grid only",
        )
        bands = []
        for band in range(1, source.count + 1):
            bands.append(
                {
                    "band": band,
                    "metadata": {
                        k: v for k, v in source.tags(band).items() if k.startswith("GRIB_")
                    },
                }
            )
        shape = {
            "width": source.width,
            "height": source.height,
            "bands": source.count,
            "bounds": list(source.bounds),
            "resolution": list(source.res),
            "crs": str(source.crs),
        }
    require(digest(path) == original_sha, "Original companion bytes unchanged")
    out = (
        ROOT
        / "outputs/reports/dataset/fwi_grib_metadata_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    result = {
        "status": "GRIB_companion_header_inspected_not_time_or_feature_admission",
        "input_path": path.relative_to(ROOT).as_posix(),
        "input_sha256": original_sha,
        "input_bytes": path.stat().st_size,
        "GRIB_edition": edition,
        "shape_metadata": shape,
        "band_metadata": bands,
        "FWI_values_decoded": False,
        "time_policy_accepted": False,
        "forecast_issue_or_operational_availability_verified": False,
        "new_features_models_or_labels_created": 0,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    main(parser.parse_args().file)
