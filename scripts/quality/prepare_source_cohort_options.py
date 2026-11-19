"""Prepare a fit-only source-cohort decision basis; do not assign possible L or Y."""

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import geopandas as gpd
from prepare_source_sampling_review import (
    ARCHIVE,
    CLOCK,
    GEO,
    GRID,
    LINK_FIELDS,
    PINS,
    PROVINCES,
    filtered_rows,
    source_windows,
)
from pyproj import Transformer
from shapely.geometry import Point

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
FRAME = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/source_frame_keys.csv"
FRAME_SHA = "56d545546059d3d675125ba96677059614d8eedf4310b13daf5f08b851e0fc44"
RETENTION = BASE / "wf1538_review_retention_v1/20261119T184009Z_0bd7da1f/readback.json"
RETENTION_SHA = "ed94ee3daa0fcfb9141ab651adb27ecde152023d4f798ab4aefbb8812b551848"
PILOT = BASE / "marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json"
PILOT_SHA = "89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476"
U_SAMPLE = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/U_key_sample.csv"
U_SHA = "fd77c27454083e45f625e7e94ef0a14e5ace7d65636cace59b92261666c4d19f"
SALUR = BASE / "source_linked_L_proposal_v1/20261119T121351Z_2d9aeb30/readback.json"
SALUR_SHA = "d0a09ecb249eb81d75e4494beaf0ca9989092c813ddd6b40e4acf0817576ab3e"
SAMPLE = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/frozen_selected_keys.csv"
SAMPLE_SHA = "e8dfaa9130658cc0072ded7834d473d24689ec616fd91c04aed6bf5fd5ea05dd"


def clock_options(geography, clocks):
    """Signatures are provisional links, not shared anonymous IDs or physical identities."""
    for row in geography + clocks:
        require(row["year"] in {str(y) for y in range(2018, 2023)}, "Fit-role rows only")
        require(date.fromisoformat(row["date"]).year == int(row["year"]), "Source year/date")
    counts = Counter(tuple(r[k] for k in LINK_FIELDS) for r in geography)
    indexed = defaultdict(list)
    for row in clocks:
        indexed[tuple(row[k] for k in LINK_FIELDS)].append(row)
    result = {}
    for row in geography:
        key = tuple(row[k] for k in LINK_FIELDS)
        matches = indexed[key]
        unique = counts[key] == len(matches) == 1
        windows = source_windows(row, matches[0]["ignition_hour"] if unique else None)
        days = sorted({w["diagnostic_window_start_utc"] for w in windows})
        require(row["event_id"] not in result, "Unique geography source key")
        result[row["event_id"]] = {
            "temporary_clock_signature_unique": unique,
            "clock_hypotheses": windows,
            "conditional_target_window_starts": days,
            "same_window_in_both_clock_hypotheses": len(windows) == 2 and len(days) == 1,
            "all_clock_hypotheses_in_current_fit": bool(windows)
            and all(w["inside_current_fit_role"] for w in windows),
            "clock_standard_verified": False,
            "physical_event_identity_verified": False,
        }
    return result


def point_options(row, grid, boundary, project):
    point = Point(float(row["longitude"]), float(row["latitude"]))
    in_province = bool(boundary.covers(point))
    qc = row["coordinate_qc_pass"] == "True"
    cells = (
        sorted(
            grid.loc[grid.geometry.covers(Point(*project.transform(point.x, point.y))), "grid_id"]
        )
        if in_province and qc
        else []
    )
    return {
        "published_coordinate_QC_pass": qc,
        "published_point_in_Mersin": in_province,
        "conditional_center_grid_ids": cells,
        "conditional_center_in_single_grid": len(cells) == 1,
        "source_coordinate_is_ignition_verified": False,
        "location_error_bound_known": False,
        "point_forced_to_nearest_grid": False,
    }


def assemble(geography, clocks, grid, boundary, project):
    times = clock_options(geography, clocks)
    rows = []
    for row in sorted(geography, key=lambda r: (r["year"], r["event_id"])):
        item = {
            "archive_row": row["event_id"],
            "year": int(row["year"]),
            "reported_date": row["date"],
            **times[row["event_id"]],
            **point_options(row, grid, boundary, project),
            "researcher_retained_outside_L": row["event_id"] == "WF1538",
            "membership": "review_unassigned",
            "target": None,
        }
        item["metadata_transportable_under_center_and_clock_hypotheses"] = all(
            item[k]
            for k in (
                "conditional_center_in_single_grid",
                "temporary_clock_signature_unique",
                "same_window_in_both_clock_hypotheses",
                "all_clock_hypotheses_in_current_fit",
            )
        )
        rows.append(item)
    return rows


def summarize_key_collisions(rows):
    """Describe shared conditional keys, without merging source records into fires."""
    grouped = defaultdict(list)
    for row in rows:
        if (
            row["metadata_transportable_under_center_and_clock_hypotheses"]
            and not row["researcher_retained_outside_L"]
        ):
            key = (
                row["conditional_center_grid_ids"][0],
                row["conditional_target_window_starts"][0],
            )
            grouped[key].append(row["archive_row"])
    return {
        "source_rows": sum(map(len, grouped.values())),
        "distinct_conditional_cell_days": len(grouped),
        "shared_conditional_cell_days": [
            {"grid_id": k[0], "window_start_utc": k[1], "source_rows": sorted(ids)}
            for k, ids in sorted(grouped.items())
            if len(ids) > 1
        ],
        "same_cell_day_proves_same_physical_event": False,
        "source_records_deduplicated_or_merged": False,
    }


def main():
    pins = {
        **PINS,
        FRAME: FRAME_SHA,
        RETENTION: RETENTION_SHA,
        PILOT: PILOT_SHA,
        SALUR: SALUR_SHA,
        U_SAMPLE: U_SHA,
        SAMPLE: SAMPLE_SHA,
        ROOT / "scripts/quality/prepare_source_sampling_review.py": (
            "67c2954261f1ecfe7837cfe7bbf2f2123c0153dab9d480521742bb972569f1f1"
        ),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Source, frame, decision and code pins")
    for receipt in (SALUR, PILOT):
        for name, sha in json.loads(receipt.read_bytes())["artifact_sha256"].items():
            require(Path(name).name == name, "Receipt artifact stays in its original folder")
            pins[receipt.parent / name] = sha
    require(all(digest(p) == h for p, h in pins.items()), "Prior L artifacts and review index")
    decision = json.loads(RETENTION.read_bytes())["decision"]
    require(
        decision["archive_row"] == "WF1538"
        and decision["membership"] == "review_unassigned"
        and decision["selected_option"] == "A_retain_review_unassigned",
        "Preserve explicit researcher retention decision",
    )
    with ZipFile(ARCHIVE) as archive:
        geography, clocks = filtered_rows(archive, GEO), filtered_rows(archive, CLOCK)
    with FRAME.open(encoding="utf-8", newline="") as stream:
        frame = {(r["archive_row"], r["year"]) for r in csv.DictReader(stream)}
    require(len(geography) == 424, "Full frozen source frame")
    require({(r["event_id"], r["year"]) for r in geography} == frame, "Same 424 source keys")
    grid = gpd.read_file(GRID).to_crs(6933)
    province = gpd.read_file(PROVINCES)
    boundary = province.loc[province.GAUL1_CODE.astype(str).eq("3160"), "geometry"].iloc[0]
    rows = assemble(
        geography, clocks, grid, boundary, Transformer.from_crs(4326, 6933, always_xy=True)
    )
    flags = (
        "published_coordinate_QC_pass",
        "published_point_in_Mersin",
        "conditional_center_in_single_grid",
        "temporary_clock_signature_unique",
        "same_window_in_both_clock_hypotheses",
        "all_clock_hypotheses_in_current_fit",
        "metadata_transportable_under_center_and_clock_hypotheses",
        "researcher_retained_outside_L",
    )
    counts = {k: sum(r[k] for r in rows) for k in flags}
    counts["transportable_excluding_researcher_retained_WF1538"] = sum(
        r["metadata_transportable_under_center_and_clock_hypotheses"]
        and not r["researcher_retained_outside_L"]
        for r in rows
    )
    report = {
        "status": "full_fit_source_frame_options_prepared_method_direction_pending",
        "scope": "same_published_424_rows_not_new_events_or_L_admission",
        "source_frame_rows": len(rows),
        "metadata_transportability_is_label_eligibility": False,
        "reported_clock_is_first_satellite_detection": False,
        "four_province_population_representativeness_verified": False,
        "source_year_counts": dict(Counter(str(r["year"]) for r in rows)),
        "counts": counts,
        "conditional_key_collisions_excluding_WF1538": summarize_key_collisions(rows),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "rows": rows,
        "independent_event_identity_or_origin_role_resolved": False,
        "source_record_is_real_positive_label": False,
        "source_L_positive_enrichment_verified": False,
        "source_selection_class_conditionals_verified": False,
        "noise_rate_or_class_prior_estimated": False,
        "previous_two_possible_L_proposals_changed": False,
        "previous_U_sample_changed": False,
        "frozen_ten_source_sample_changed": False,
        "satellite_results_used_for_selection": False,
        "habitat_results_used_for_selection": False,
        "new_L_memberships": 0,
        "binary_labels_created": 0,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
    }
    out = (
        BASE
        / "source_cohort_options_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "readback.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Saved readback")
    require(all(digest(p) == h for p, h in pins.items()), "Inputs unchanged at closure")
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(counts))
    print("PASS same_424_source_rows_uncertainty_retained; not L, labels or method acceptance")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
