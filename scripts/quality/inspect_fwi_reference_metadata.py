"""Inspect a bounded local FWI NetCDF header, without reading fire-index arrays or admitting X."""

import argparse
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import rasterio

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/fwi_reference_pilot_v1.json"


def nominal_cf_times(units, values):
    match = re.fullmatch(r"(hours|days|seconds) since (.+)", units.strip())
    require(match is not None, "Recognized explicit CF time units")
    origin = datetime.fromisoformat(match[2].replace("Z", "+00:00"))
    if origin.tzinfo is None:
        origin = origin.replace(tzinfo=UTC)
    factors = {"seconds": 1, "hours": 3600, "days": 86400}
    parsed = [
        (origin + timedelta(seconds=float(x) * factors[match[1]])).astimezone(UTC) for x in values
    ]
    require(
        parsed and all(t.year == 2022 and t.month == 6 for t in parsed),
        "Only June 2022 pilot nominal times",
    )
    return [t.astimezone(UTC).isoformat() for t in parsed]


def main(path):
    config = json.loads(CONFIG.read_bytes())
    path = path.resolve()
    raw = (ROOT / config["raw_directory"]).resolve()
    require(
        path.is_relative_to(raw) and path.is_file() and path.suffix.lower() == ".nc",
        "Local requested pilot NetCDF only",
    )
    require(
        path.stat().st_size <= config["max_local_file_bytes"],
        "Bounded regional file; retain unexpected files for separate review",
    )
    with path.open("rb") as stream:
        signature = stream.read(8)
    require(
        signature.startswith(b"CDF") or signature == b"\x89HDF\r\n\x1a\n",
        "Actual NetCDF/HDF container, not an HTML login page",
    )
    file_sha = digest(path)
    with rasterio.Env():
        with rasterio.open(path) as root_dataset:
            subdatasets = root_dataset.subdatasets
            candidates = [
                p
                for p in subdatasets
                if p.rsplit(":", 1)[-1].lower() in {"fwi", "fire_weather_index"}
            ]
            if subdatasets:
                require(
                    len(candidates) == 1, "Exactly one recognized FWI variable; no guessed array"
                )
                target = candidates[0]
                require("http" not in target.lower(), "Never open a remote subdataset")
            else:
                target = str(path)
        with rasterio.open(target) as dataset:
            tags = dataset.tags()
            time_names = [
                n
                for n in ("time", "valid_time")
                if f"NETCDF_DIM_{n}_VALUES" in tags and f"{n}#units" in tags
            ]
            nominal = None
            if len(time_names) == 1:
                n = time_names[0]
                raw_values = tags[f"NETCDF_DIM_{n}_VALUES"].strip("{} ").split(",")
                nominal = nominal_cf_times(tags[f"{n}#units"], raw_values)
            require(
                dataset.width <= 100 and dataset.height <= 100 and dataset.count <= 31,
                "Small regional monthly metadata shape",
            )
            metadata = {
                "driver": dataset.driver,
                "width": dataset.width,
                "height": dataset.height,
                "bands": dataset.count,
                "crs": str(dataset.crs),
                "bounds": list(dataset.bounds),
                "resolution": list(dataset.res),
                "nominal_CF_times": nominal,
                "time_metadata_supported": nominal is not None,
                "variable_names": [p.rsplit(":", 1)[-1] for p in subdatasets],
                "metadata_fields": {
                    k: v[:1000]
                    for k, v in tags.items()
                    if k.endswith(("#units", "#long_name", "#standard_name"))
                    or k.startswith("NETCDF_DIM_")
                },
            }
    require(digest(path) == file_sha, "Original provider bytes unchanged")
    out = (
        ROOT
        / "outputs/reports/dataset/fwi_reference_metadata_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    report = {
        "status": (
            "local_FWI_header_inspected_time_alignment_and_scientific_admission_still_pending"
        ),
        "input_path": path.relative_to(ROOT).as_posix(),
        "input_sha256": file_sha,
        "input_bytes": path.stat().st_size,
        "metadata": metadata,
        "scientific_FWI_array_values_read": False,
        "FWI_admitted_as_feature_or_fire_probability": False,
        "new_labels_or_models_created": 0,
        "final_merge_performed": False,
        "config_sha256": digest(CONFIG),
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    main(parser.parse_args().file)
