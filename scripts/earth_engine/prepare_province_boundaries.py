"""Explicit read-only four-province GAUL fetch; never create EE exports or change the AOI."""

import argparse
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import ee
import geopandas as gpd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
ASSET = "FAO/GAUL/2025/level1"
NAMES = ["Antalya", "Mugla", "Muğla", "Izmir", "İzmir", "Mersin", "Icel", "İçel", "Içel"]
CANONICAL = {
    "Antalya": "Antalya",
    "Mugla": "Muğla",
    "Muğla": "Muğla",
    "Izmir": "İzmir",
    "İzmir": "İzmir",
    "Mersin": "Mersin",
    "Icel": "Mersin",
    "İçel": "Mersin",
    "Içel": "Mersin",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch():
    load_dotenv(ROOT / ".env", override=False)
    project = os.getenv("GEE_PROJECT_ID", "").strip()
    if not project:
        raise ValueError("Earth Engine project not configured")
    before = sha(ROOT / "data/aoi/aoi.geojson")
    ee.Initialize(project=project)
    ee.data.setDeadline(60000)
    source = ee.FeatureCollection(ASSET).filter(ee.Filter.eq("ISO3_CODE", "TUR"))
    source = source.filter(ee.Filter.inList("GAUL1_NAME", NAMES))
    value = source.select(["ISO3_CODE", "GAUL1_CODE", "GAUL1_NAME"]).getInfo()
    frame = gpd.GeoDataFrame.from_features(value["features"], crs=4326)
    if len(frame) != 4 or not frame.geometry.is_valid.all() or frame.GAUL1_CODE.nunique() != 4:
        raise ValueError("Expected four valid unique GAUL provinces")
    frame["province"] = frame.GAUL1_NAME.map(CANONICAL)
    if set(frame.province) != {"Antalya", "Muğla", "İzmir", "Mersin"}:
        raise ValueError("Province identity mismatch")
    if before != sha(ROOT / "data/aoi/aoi.geojson"):
        raise ValueError("Original AOI changed")
    out = (
        ROOT
        / "data/raw/boundaries/gaul2025"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "provinces.geojson"
    frame.sort_values("province").to_file(path, driver="GeoJSON", index=False)
    saved = gpd.read_file(path)
    if set(saved.province) != set(frame.province) or not saved.geometry.is_valid.all():
        raise ValueError("Province file readback")
    record = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed",
        "source": ASSET,
        "source_country": "TUR",
        "source_reference_year": 2025,
        "purpose": "geography_audit_only_not_historical_feature",
        "original_aoi_sha256": before,
        "boundary_sha256": sha(path),
        "script_sha256": sha(Path(__file__)),
        "province_count": len(saved),
        "attribution": "FAO. 2025. Global Administrative Unit Layers (GAUL). CC-BY-4.0",
        "export_tasks_created": 0,
        "vm_changes": False,
        "limits": [
            "Same boundary edition as original AOI, no historical boundary claim",
            "Original AOI union used 10m EE tolerance; local mismatch must be measured",
        ],
    }
    (out / "readback.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Province boundary source:", out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", required=True)
    parser.parse_args()
    try:
        fetch()
    except Exception as error:
        print("Boundary source unavailable:", type(error).__name__)
        raise SystemExit(1) from None
