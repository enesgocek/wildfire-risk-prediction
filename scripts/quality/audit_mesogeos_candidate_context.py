"""Read saved 32-case context with direct raster windows and standard-library clock arithmetic."""

import csv
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import rasterio
from pyproj import Geod, Transformer
from rasterio.windows import Window

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.landscape import FOREST_CODES

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "mesogeos_candidate_context_v1/20261124T234645Z_8d88cfe5"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    report = json.loads((RUN / "readback.json").read_bytes())
    for name, expected in report["input_sha256"].items():
        require(digest(ROOT / name) == expected, "Immutable context inputs")
    for name, expected in report["artifact_sha256"].items():
        require(digest(RUN / name) == expected, "Saved context artifacts")
    cases, scenarios = rows(RUN / "case_context.csv"), rows(RUN / "conditional_S_proposals.csv")
    points_path = next(
        ROOT / p for p in report["input_sha256"] if p.endswith("point_context_review.csv")
    )
    points = {r["source_record_index"]: r for r in rows(points_path)}
    link_path = next(
        ROOT / p for p in report["input_sha256"] if p.endswith("native_date_context_lookup.csv")
    )
    expected_ids = {
        r["source_record_index"]
        for r in rows(link_path)
        if r["calendar_lookup_only"] != "existing_S_context"
    }
    require(
        len(cases) == 32 and {r["source_record_index"] for r in cases} == expected_ids,
        "Approved exact 32 cases",
    )
    raster_keys = {
        "cgls2017": next(
            p for p in report["input_sha256"] if p.endswith("landcover_copernicus_2017.tif")
        ),
        "corine2018": next(
            p for p in report["input_sha256"] if p.endswith("U2018_CLC2018_V2020_20u1.tif")
        ),
    }
    legend_path = next(
        ROOT / p
        for p in report["input_sha256"]
        if "corine_delivery_review_v1" in p and p.endswith("readback.json")
    )
    legend = json.loads(legend_path.read_bytes())["legend"]
    for prefix, path in raster_keys.items():
        with rasterio.open(ROOT / path) as source:
            transform = Transformer.from_crs(4326, source.crs, always_xy=True)
            for row in cases:
                point = points[row["source_record_index"]]
                x, y = transform.transform(
                    float(point["native_point_lon"]), float(point["native_point_lat"])
                )
                rr, cc = source.index(x, y)
                value = source.read(1, window=Window(cc, rr, 1, 1), masked=True)[0, 0]
                require(not value.mask if hasattr(value, "mask") else True, "Mapped pixel context")
                raw = int(value)
                code = raw if prefix == "cgls2017" else legend[str(raw)]["clc_code"]
                require(
                    raw == int(row[prefix + "_raw_raster_value"])
                    and code == int(row[prefix + "_class_code"]),
                    "Direct native raster cell readback",
                )
                require(
                    rr == int(row[prefix + "_raster_row"])
                    and cc == int(row[prefix + "_raster_column"]),
                    "Native cell addressing",
                )
                woody = code in (
                    {*FOREST_CODES, 20} if prefix == "cgls2017" else {311, 312, 313, 322, 323, 324}
                )
                require(
                    woody == (row[prefix + "_point_context"] == "forest_shrub"),
                    "Primary and auxiliary woody definitions",
                )
    detection_path = next(
        ROOT / p for p in report["input_sha256"] if p.endswith("historical_center_context.csv")
    )
    detections = [
        (
            datetime.fromisoformat(r["detection_timestamp_utc"]),
            float(r["longitude"]),
            float(r["latitude"]),
        )
        for r in rows(detection_path)
    ]
    require(
        len(detections) == 28396 and all(2018 <= t.year <= 2022 for t, _, _ in detections),
        "No closed-year values",
    )
    by_id = {r["source_record_index"]: r for r in cases}
    geod = Geod(ellps="WGS84")
    groups = {}
    for case_id, case in by_id.items():
        point = points[case_id]
        original = datetime.fromisoformat(case["conditional_acquisition_utc"])
        longitude, latitude = float(point["native_point_lon"]), float(point["native_point_lat"])
        for clock in (
            "preserved_MODIS_UTC_if_lineage_correct",
            "minus_3h_stress_only_not_claimed_local_time",
        ):
            stamp = original - timedelta(hours=0 if clock.startswith("preserved") else 3)
            groups[(case_id, clock)] = [
                (t, abs(geod.inv(longitude, latitude, lon, lat)[2]))
                for t, lon, lat in detections
                if stamp - timedelta(hours=72) <= t <= stamp + timedelta(hours=24)
            ]
    signatures = {}
    conditional_dates = {}
    for row in scenarios:
        case_id, clock = row["source_record_index"], row["clock_assumption"]
        case = by_id[case_id]
        stamp = datetime.fromisoformat(case["conditional_acquisition_utc"]) - timedelta(
            hours=0 if clock.startswith("preserved") else 3
        )
        radius, hours = int(row["distance_m"]), int(row["history_hours"])
        nearby = [t for t, distance in groups[(case_id, clock)] if distance <= radius]
        earlier = sum(stamp - timedelta(hours=hours) <= t < stamp for t in nearby)
        same = sum(t == stamp for t in nearby)
        later = sum(stamp < t <= stamp + timedelta(hours=24) for t in nearby)
        require(
            [earlier, same, later]
            == [
                int(row[k])
                for k in (
                    "earlier_VIIRS_centers",
                    "simultaneous_VIIRS_centers",
                    "later_24h_VIIRS_centers",
                )
            ],
            "Scalar geodesic/standard clock context counts",
        )
        prediction = (stamp - timedelta(microseconds=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        require(
            prediction.isoformat() == row["conditional_prediction_timestamp_utc"],
            "Right-closed target boundary",
        )
        allowed = prediction >= datetime(2018, 1, 1, tzinfo=UTC) and prediction + timedelta(
            days=1
        ) < datetime(2023, 1, 1, tzinfo=UTC)
        proposal = (
            allowed
            and case["water_scope_included"] == "True"
            and case["cgls2017_point_context"] == "forest_shrub"
            and earlier == 0
            and stamp - timedelta(hours=hours) >= datetime(2018, 1, 1, tzinfo=UTC)
        )
        require(
            proposal == (row["conditional_S_proposal_only"] == "True"),
            "Explicit conditional preparation rule, not accepted membership",
        )
        require(
            not row["target"]
            and not row["accepted_L_membership"]
            and row["accepted_S_assignment"] == row["negative_label_permitted"] == "False",
            "No scientific acceptance",
        )
        signatures.setdefault(case_id, []).append(proposal)
        conditional_dates.setdefault(case_id, set()).add(prediction.isoformat())
    summaries = []
    for case_id, flags in signatures.items():
        require(len(flags) == 18, "Both clocks and nine settings")
        require(
            (len(conditional_dates[case_id]) == 1)
            == (by_id[case_id]["conditional_target_day_stable_under_3h_stress"] == "True"),
            "Day sensitivity readback",
        )
        summaries.append(
            {
                "source_id": by_id[case_id]["source_id"],
                "source_record_index": case_id,
                "conditional_proposals_of_18": sum(flags),
                "proposal_stable_all_18_and_day": all(flags)
                and len(conditional_dates[case_id]) == 1,
                "target_day_count_under_clock_stress": len(conditional_dates[case_id]),
                "scientific_label_accepted": False,
            }
        )
    out = (
        BASE
        / "mesogeos_candidate_context_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    with (out / "case_sensitivity.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    result = {
        "status": "32_cases_direct_raster_and_scalar_time_context_audited_not_truth",
        "analysis_date": "2026-11-25",
        "review_receipt_sha256": digest(RUN / "readback.json"),
        "cases_checked": len(cases),
        "scenario_rows_checked": len(scenarios),
        "stable_proposal_and_day_rows": sum(r["proposal_stable_all_18_and_day"] for r in summaries),
        "conditional_proposal_support_distribution": dict(
            Counter(r["conditional_proposals_of_18"] for r in summaries)
        ),
        "day_sensitive_case_rows": sum(
            r["target_day_count_under_clock_stress"] > 1 for r in summaries
        ),
        "new_S_or_Y_or_L_assignments": False,
        "final_merge": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "auditor_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
