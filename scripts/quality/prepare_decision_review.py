"""Offline habitat/weather support and traceable event-case packet from accepted inputs."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd
from shapely.geometry import shape

from wildfire_risk_prediction.decision_review import (
    VERSION,
    event_cases,
    habitat_cases,
    support_intersection,
)
from wildfire_risk_prediction.event_review import training_detections
from wildfire_risk_prediction.feature_join import require

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HABITAT = "outputs/reports/habitat/review_v1/20261009T235212Z_3c2c021b"
EVENTS = "outputs/reports/events/review_v1/20261010T001137Z_320433ed"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    inputs = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular retained input")
        digest = sha(path)
        require(expected is None or digest == expected, "Source changed")
        inputs[name] = digest
        return path

    def record(name, expected=None):
        return json.loads(retained(name, expected).read_text())

    habitat_report = record(
        HABITAT + "/review.json", "326c1c0197f3cb46aafbf6f4ee62478d1953ad3975fc13f99f9a6c5de3d31d5b"
    )
    habitat = pd.read_csv(retained(HABITAT + "/cells.csv", habitat_report["review_table_sha256"]))
    require(
        habitat_report["habitat_eligibility_decided"] is False
        and habitat_report["final_test_accessed"] is False,
        "Habitat scope",
    )
    static_manifest = record(
        "data/interim/landscape/v1/manifest.json", habitat_report["static_manifest_sha256"]
    )
    retained("data/interim/landscape/v1/grid_static.csv", habitat_report["static_table_sha256"])
    parts = record("data/interim/grid_aoi_parts.geojson", static_manifest["parts_sha256"])
    require(
        parts["crs"]["properties"]["name"] == "urn:ogc:def:crs:OGC:1.3:CRS84",
        "Geometry coordinate system",
    )
    policy = record("data/interim/meteorology/model_v1/policy_manifest.json")
    weather_report = record(policy["review"], policy["review_sha256"])
    require(
        weather_report["selection_period"] == [2018, 2023]
        and weather_report["validation_used_for_rule_selection"] is False
        and weather_report["final_test_accessed"] is False
        and weather_report["constant_coverage_all_training_days"] is True,
        "Weather scope",
    )
    coverage = pd.read_csv(
        retained(
            "data/interim/meteorology/model_v1/training_grid_coverage.csv",
            weather_report["grid_coverage_sha256"],
        )
    )
    table, groups, sensitivity = support_intersection(habitat, coverage)
    require(
        len(table) == 2899 and weather_report["counts"]["rows"] % len(table) == 0,
        "Training row count",
    )
    days = weather_report["counts"]["rows"] // len(table)
    counts = {g["support_group"]: g["cells"] for g in groups}
    require(
        counts["none"] * days == weather_report["counts"]["weather_missing_any"]
        and counts["partial"] * days == weather_report["counts"]["weather_partial_area"]
        and counts["full"] * days == weather_report["counts"]["weather_primary_eligible"],
        "Independent aggregate weather reconciliation",
    )
    old_sensitivity = {
        (s["measure"], s["exploratory_threshold_inclusive"]): s["cells_at_or_above"]
        for s in habitat_report["sensitivity"]
    }
    require(
        all(
            s["cells"] == old_sensitivity[(s["measure"], s["threshold_inclusive"])]
            for s in sensitivity
        ),
        "Habitat sensitivity reconciliation",
    )
    cells = habitat_cases(table)
    geometries = {f["properties"]["grid_id"]: f["geometry"] for f in parts["features"]}
    require(set(geometries) == set(table.grid_id), "Map keys")
    points = cells.grid_id.map(lambda g: shape(geometries[g]).representative_point())
    cells["review_point_longitude"] = points.map(lambda p: p.x)
    cells["review_point_latitude"] = points.map(lambda p: p.y)
    event_report = record(
        EVENTS + "/review.json", "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e"
    )
    require(
        event_report["labels_created"] is False
        and event_report["scenario_selected"] is None
        and event_report["final_test_accessed"] is False,
        "Event scope",
    )
    source = pd.read_csv(
        retained(
            "data/interim/firms_combined_candidates_2018_2024.csv", event_report["source_sha256"]
        ),
        dtype="string",
    )
    years = pd.to_datetime(source.detection_timestamp_utc, format="ISO8601", utc=True).dt.year
    require(years.between(2018, 2024).all(), "No final-test source")
    detections = training_detections(source.loc[years.le(2023)])
    require(len(detections) == event_report["training_detection_count"], "Training candidates")
    by_detection = detections.set_index("detection_id")
    by_grid = table.set_index("grid_id")
    cases, members = [], []
    for scenario, digests in sorted(event_report["artifact_sha256"].items()):
        catalog = pd.read_csv(
            retained(EVENTS + f"/{scenario}_review.csv", digests["review_sha256"])
        )
        selected = event_cases(catalog)
        assignments = pd.read_csv(
            retained(
                f"data/interim/event_grouping/{scenario}_assignments.csv",
                digests["assignments_sha256"],
            ),
            dtype="string",
        )
        require(
            assignments.detection_id.is_unique
            and set(assignments.detection_id) == set(by_detection.index),
            "Assignment keys",
        )
        ordered = assignments.set_index("detection_id").loc[by_detection.index]
        require(ordered.grid_id.eq(by_detection.grid_id).all(), "Assignment grid identity")
        require(
            pd.to_datetime(ordered.timestamp, format="ISO8601", utc=True)
            .eq(by_detection.timestamp)
            .all(),
            "Assignment timestamp identity",
        )
        for row in selected.itertuples():
            ids = assignments.loc[assignments.cluster_id.eq(row.cluster_id), "detection_id"]
            group = by_detection.loc[ids].sort_values(["timestamp", "detection_id"])
            require(
                hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest() == row.membership_sha256
                and len(group) == row.detection_count,
                "Case membership",
            )
            first = group.timestamp.min()
            first_grids = sorted(group.loc[group.timestamp.eq(first), "grid_id"].unique())
            require(
                first.isoformat() == row.first_detection_utc
                and group.timestamp.max().isoformat() == row.last_detection_utc
                and first_grids == json.loads(row.earliest_grid_ids_json),
                "Case first/last/cells",
            )
            fractions = by_grid.loc[first_grids, "forest_shrub_fraction"]
            selected.loc[selected.cluster_id.eq(row.cluster_id), "first_cell_min_forest_shrub"] = (
                fractions.min()
            )
            selected.loc[selected.cluster_id.eq(row.cluster_id), "first_cell_max_forest_shrub"] = (
                fractions.max()
            )
            payload = group.reset_index()
            payload["scenario"] = scenario
            payload["cluster_id"] = row.cluster_id
            members.append(payload.drop(columns="timestamp"))
        selected["scenario"] = scenario
        cases.append(selected)
    selected_cases = pd.concat(cases, ignore_index=True)
    selected_members = pd.concat(members, ignore_index=True)
    for name in [
        "src/wildfire_risk_prediction/decision_review.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/weather_policy.py",
        __file__,
    ]:
        retained(Path(name).relative_to(ROOT).as_posix() if Path(name).is_absolute() else name)
    out = (
        ROOT
        / "outputs/reports/dataset/decision_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    for name, frame in [
        ("support_cells.csv", table),
        ("habitat_cases.csv", cells),
        ("event_cases.csv", selected_cases),
        ("event_members.csv", selected_members),
    ]:
        frame.to_csv(out / name, index=False)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True),
            pd.read_csv(
                out / name, dtype={"type": "string"} if name == "event_members.csv" else None
            ),
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    form = pd.DataFrame(
        {
            "case_kind": ["habitat"] * len(cells) + ["event"] * len(selected_cases),
            "case_key": cells.grid_id.tolist()
            + (selected_cases.scenario + ":" + selected_cases.cluster_id).tolist(),
        }
    )
    for field in [
        "reviewer",
        "reviewed_at_utc",
        "evidence_reference",
        "interpretation",
        "decision",
    ]:
        form[field] = ""
    form.to_csv(out / "expert_review_template.csv", index=False)
    geo = gpd.GeoDataFrame.from_features(parts["features"], crs="EPSG:4326").to_crs("EPSG:6933")
    geo = geo.merge(
        table[["grid_id", "weather_support_group", "water_only_flag", "terrain_area_review_flag"]],
        on="grid_id",
        validate="one_to_one",
    )
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), layout="constrained")
    palette = {"none": "#c44e52", "partial": "#ddaa33", "full": "#548c6c"}
    for group, color in palette.items():
        geo.loc[geo.weather_support_group.eq(group)].plot(ax=axes[0], color=color, linewidth=0)
    axes[0].set_title(
        "Meteoroloji destek grupları — 2018–2023 / kırmızı: yok, sarı: kısmi, yeşil: tam"
    )
    geo.plot(ax=axes[1], color="#e3e7eb", linewidth=0)
    for field, color, label in [
        ("water_only_flag", "#3478b3", "2017 haritasında yalnız su"),
        ("terrain_area_review_flag", "#a64c96", "Arazi alan desteği incelemesi"),
    ]:
        centers = geo.loc[geo[field]].geometry.representative_point()
        axes[1].scatter(centers.x, centers.y, c=color, s=25, label=label)
    axes[1].legend(loc="lower right")
    axes[1].set_title(
        "Harita sınıfı ve alan desteği işaretleri — uygunluk veya yangın etiketi değildir"
    )
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_axis_off()
    fig.savefig(out / "support_review.png", dpi=140)
    plt.close(fig)
    require(
        all(sha(ROOT / name) == digest for name, digest in inputs.items()), "Retained input changed"
    )
    report = {
        "status": "decision_review_packet_readback_passed",
        "version": VERSION,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "inputs_sha256": inputs,
        "artifact_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
        "support_groups": groups,
        "sensitivity": sensitivity,
        "training_days": days,
        "habitat_cases": len(cells),
        "event_scenario_cases": len(selected_cases),
        "unique_event_membership_patterns": selected_cases.membership_sha256.nunique(),
        "event_member_rows_with_scenario_repetition": len(selected_members),
        "validation_rows_read_for_period_filter": int(years.eq(2024).sum()),
        "validation_used_for_rule_selection": False,
        "retained_inputs_unchanged": True,
        "threshold_selected": None,
        "scenario_selected": None,
        "labels_created": False,
        "negative_label_permitted": False,
        "final_test_accessed": False,
        "habitat_eligibility_decided": False,
        "independent_expert_review_completed": False,
        "limits": [
            "Purposive examples; not representative prevalence or confirmed fires",
            "Cross-scenario cases and detections overlap; not independent counts",
            "2017 class map and retrospective reanalysis; operational availability unknown",
            "Old extraction/graph readbacks reused; no repeated raw extraction or graph build",
        ],
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "habitat_cases": len(cells),
                "event_scenario_cases": len(selected_cases),
                "report": (out / "readback.json").relative_to(ROOT).as_posix(),
            }
        )
    )


if __name__ == "__main__":
    main()
