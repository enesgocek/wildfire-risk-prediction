"""Offline spatial reference audit from bounded, hash-pinned historical downloads."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.perimeter_review import effis_gml, medeu_inventory, spatial_context

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EFFIS = "data/raw/reference/effis/2021_summer_pilot_2026-10-14/effis_2021_summer.gml"
EFFIS_SHA = "351506b52949e292aaaf62b51556ae0cfd9d553c2c198d24b81ecdb758e65eba"
MEDEU = "data/raw/reference/firespread_medeu/18200075/FireSpread_MedEU.zip"
MEDEU_SHA = "907e8d340bd44cde64c739b39474381d72ebe64aeef86c0daba17fa53967e27b"
AOI = "data/aoi/aoi.geojson"
AOI_SHA = "d727a6c1e320650a47fd18c7077af847a82d4c99cdc87e49a3c32cb144ea7c22"
PACKET = "outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e"
PACKET_SHA = "36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037"
DECISION = "outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2"
MEMBER_SHA = "bb24d25379acde97d65edd7bcff93e07b2b0ec61f84adb811ecfcf06e958c391"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline perimeter audit")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular reference input")
        digest = sha(path)
        require(expected is None or digest == expected, "Pinned perimeter source changed")
        pins[name] = digest
        return path

    packet = json.loads(retained(PACKET + "/readback.json", PACKET_SHA).read_text())
    require(
        packet["labels_created"] is False and packet["model_ready"] is False,
        "Unlabelled review packet",
    )
    cases = pd.read_csv(
        retained(
            PACKET + "/purposive_event_cases.csv",
            packet["artifact_sha256"]["purposive_event_cases.csv"],
        )
    )
    members = pd.read_csv(retained(DECISION + "/event_members.csv", MEMBER_SHA))
    aoi_path = retained(AOI, AOI_SHA)
    aoi = gpd.read_file(aoi_path)
    require(aoi.crs.to_epsg() == 4326 and aoi.is_valid.all(), "Accepted WGS84 pilot AOI")
    refs = effis_gml(retained(EFFIS, EFFIS_SHA).read_bytes())
    require(len(refs) == 84, "Downloaded filter count agrees with WFS hits")
    for name in (
        "data/raw/reference/effis/2021_summer_pilot_2026-10-14/receipt.json",
        "data/raw/reference/firespread_medeu/18200075/receipt.json",
        "outputs/reports/dataset/perimeter_discovery_2026-10-14/effis_schema.xml",
        "outputs/reports/dataset/perimeter_discovery_2026-10-14/effis_2021_pilot_hits.xml",
        "src/wildfire_risk_prediction/perimeter_review.py",
        "scripts/quality/review_perimeter_sources.py",
        PROTECTED,
    ):
        retained(name)
    protected = json.loads((ROOT / PROTECTED).read_text())
    for name, digest in protected.items():
        retained(name, digest)
    medeu = gpd.read_file("zip://" + retained(MEDEU, MEDEU_SHA).as_posix())
    inventory = medeu_inventory(medeu)
    # Invalid polygons are quarantined without modifying accepted source geometries.
    burned = medeu.loc[inventory.training_burned_reference_candidate]
    medeu_hits = burned.geometry.intersects(aoi.to_crs(medeu.crs).geometry.union_all())
    medeu_bounds = medeu.loc[inventory.is_burned_step].to_crs(4326).total_bounds.tolist()
    valid_refs = refs.loc[refs.geometry_valid].copy()
    valid_refs["intersects_pilot_aoi"] = valid_refs.intersects(aoi.geometry.union_all())
    pilot_refs = valid_refs.loc[valid_refs.intersects_pilot_aoi].copy()
    links, summary = spatial_context(cases, members, pilot_refs)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/perimeter_review_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("medeu_inventory.csv", inventory),
        ("effis_inventory.csv", refs.drop(columns="geometry")),
        ("case_reference_spatial_links.csv", links),
        ("case_spatial_summary.csv", summary),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        string_columns = {
            c: str
            for c in frame
            if not frame[c].dropna().empty
            and frame[c].dropna().map(lambda x: isinstance(x, str)).all()
        }
        reread = pd.read_csv(path, float_precision="round_trip", dtype=string_columns)
        pd.testing.assert_frame_equal(
            frame.astype(object).where(frame.notna(), None),
            reread.astype(object).where(reread.notna(), None),
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
        artifacts[name] = sha(path)
    # Illustrative case fixed before plotting; no event threshold or identity is selected.
    case_id = "d2000m_t72h_C003757"
    ids = links.loc[links.cluster_id.eq(case_id), "reference_id"]
    subset = pilot_refs.loc[pilot_refs.reference_id.isin(ids)]
    points = members.loc[members.cluster_id.eq(case_id)]
    fig, ax = plt.subplots(figsize=(9, 7))
    subset.plot(ax=ax, color="#c7e4ef", edgecolor="#266786", alpha=0.65)
    ax.scatter(
        points.longitude,
        points.latitude,
        s=2,
        color="#d55e00",
        alpha=0.35,
        label="VIIRS member detections; not independent fires",
    )
    for row in subset.itertuples():
        point = row.geometry.representative_point()
        ax.annotate("EFFIS " + row.reference_id, (point.x, point.y), fontsize=8)
    ax.set(
        xlabel="Longitude (degrees east)",
        ylabel="Latitude (degrees north)",
        title=(
            "2021 exploratory cluster and EFFIS final perimeters\n"
            "Spatial context only; shared sensor lineage"
        ),
    )
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "spatial_context.png", dpi=160)
    plt.close(fig)
    artifacts["spatial_context.png"] = sha(out / "spatial_context.png")
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Retained sources unchanged")
    result = {
        "status": "perimeter_spatial_context_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "medeu": {
            "rows": len(medeu),
            "events": int(medeu.EFFIS_id.nunique()),
            "pre_fire_context_rows": int(inventory.is_pre_fire_context.sum()),
            "burned_steps": int(inventory.is_burned_step.sum()),
            "missing_geometry_rows": int(medeu.geometry.isna().sum()),
            "invalid_burned_polygons": int(
                (inventory.is_burned_step & ~inventory.geometry_valid).sum()
            ),
            "training_pilot_overlap_steps": int(medeu_hits.sum()),
            "burned_wgs84_bounds": medeu_bounds,
            "suitable_for_pilot": bool(medeu_hits.any()),
        },
        "effis": {
            "downloaded_rows": len(refs),
            "country_counts_in_query_box": refs.COUNTRY.value_counts().to_dict(),
            "invalid_polygons_quarantined": int((~refs.geometry_valid).sum()),
            "valid_pilot_intersecting_perimeters": len(pilot_refs),
        },
        "reviewed_spatial_case_variants": len(summary),
        "case_reference_pairs": len(links),
        "variants_with_multiple_first_point_perimeters": int(
            summary.reference_count_with_first.gt(1).sum()
        ),
        "variants_with_multiple_member_perimeters": int(
            summary.reference_count_with_member.gt(1).sum()
        ),
        "plot_case_id": case_id,
        "exact_event_identities_accepted": 0,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "source_geometry_repaired": False,
        "limits": [
            "EFFIS shares MODIS/VIIRS/Sentinel lineage; not independent ground truth",
            "Final perimeter membership does not prove first-cell/day burning or ignition",
            "Missing perimeter and outside-perimeter points are not negative labels",
            "Raw reference clocks have no assumed UTC conversion",
            "Pilot is July-August 2021 only; no full calendar reference completeness claim",
        ],
    }
    (out / "readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Perimeter review result:", out.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
