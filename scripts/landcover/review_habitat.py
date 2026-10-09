"""Offline review of accepted static cells, independent of vegetation production."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.habitat_review import review_habitat

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "data/interim/landscape/v1"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_accepted_static(root):
    static = root / "data/interim/landscape/v1"
    manifest = json.loads((static / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != "landscape_retro_v1" or manifest.get("grid_count") != 2899:
        raise ValueError("Static version/grid contract")
    for name in (
        "final_test_accessed",
        "labels_created",
        "historical_availability_verified",
        "habitat_eligibility_decided",
    ):
        if manifest.get(name) is not False:
            raise ValueError(f"Static scope changed: {name}")
    if manifest.get("table") != "data/interim/landscape/v1/grid_static.csv":
        raise ValueError("Static table path changed")
    sources = {
        "table_sha256": "data/interim/landscape/v1/grid_static.csv",
        "grid_sha256": "data/aoi/grid_5km.geojson",
        "parts_sha256": "data/interim/grid_aoi_parts.geojson",
        "landcover_table_sha256": "data/interim/grid_landcover_2017.csv",
        "landcover_source_sha256": "data/raw/landcover/landcover_copernicus_2017.tif",
    }
    for key, relative in sources.items():
        if sha(root / relative) != manifest.get(key):
            raise ValueError(f"Static source hash changed: {key}")
    parts = json.loads((root / sources["parts_sha256"]).read_text(encoding="utf-8"))
    ids = [row["properties"]["grid_id"] for row in parts["features"]]
    if len(ids) != 2899 or len(set(ids)) != len(ids):
        raise ValueError("AOI grid keys")
    return pd.read_csv(static / "grid_static.csv"), ids, manifest


def main():
    frame, ids, manifest = load_accepted_static(ROOT)
    table, report = review_habitat(frame, ids)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = ROOT / "outputs/reports/habitat/review_v1" / run_id
    out.mkdir(parents=True, exist_ok=False)
    table.to_csv(out / "cells.csv", index=False, mode="x")
    saved = pd.read_csv(out / "cells.csv")
    pd.testing.assert_frame_equal(table, saved, check_dtype=False)
    report.update(
        {
            "status": "passed_static_diagnostic_readback",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "static_manifest_sha256": sha(STATIC / "manifest.json"),
            "static_table_sha256": manifest["table_sha256"],
            "review_table_sha256": sha(out / "cells.csv"),
            "source_sha256": {
                name: sha(ROOT / name)
                for name in (
                    "src/wildfire_risk_prediction/habitat_review.py",
                    "src/wildfire_risk_prediction/landscape.py",
                    "scripts/landcover/review_habitat.py",
                )
            },
            "validation_scope": "Accepted static hashes, row contracts and CSV readback; "
            "no repeated terrain integral audit or independent habitat truth",
        }
    )
    with (out / "review.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "report": (out / "review.json").relative_to(ROOT).as_posix(),
                "grid_count": len(table),
                "status": report["status"],
            }
        )
    )


if __name__ == "__main__":
    main()
