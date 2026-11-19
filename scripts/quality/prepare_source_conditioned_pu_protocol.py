"""Record the A direction and run bounded source-only geometry/time/domain diagnostics."""

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import geopandas as gpd
from prepare_source_sampling_review import ARCHIVE, GEO, GRID, PROVINCES, filtered_rows
from pyproj import Transformer
from shapely.geometry import Point

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/source_conditioned_pu_protocol_v1.json"
PARENT = BASE / "source_cohort_options_v1/20261119T195538Z_02488a97/readback.json"
PARENT_SHA = "849f0ef0ad8af1ed88eac2418ddf5c2026db0910a7a852760b710a8821387a06"
U = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/U_key_sample.csv"
WATER = BASE / "water_scope_v1/20261014T185242Z_f2e469bd/grid_water_scope.csv"
WATER_SHA = "5ab988c0b59a51a92763187359bb84588929f95926d827d6e5d177a8aa329946"


def validate_policy(p):
    require(p["version"] == "source_conditioned_pu_protocol_v1", "Versioned protocol")
    require(p["decision_parent_sha256"] == PARENT_SHA, "Decision bound to reviewed parent")
    require(
        p["decision_source"]
        == "explicit_user_selection_A_prepare_source_conditioned_PU_pilot_protocol",
        "Explicit preparation direction",
    )
    closed = (
        "main_target_changed",
        "WF1538_retention_overridden",
        "new_L_memberships_permitted",
        "satellite_results_used_for_selection",
        "habitat_results_used_for_selection",
        "resample_or_replace_frozen_ten_rows",
        "source_final_area_is_predictor",
        "source_coordinate_role_verified",
        "source_record_unit_verified",
        "source_to_first_detection_time_relation_verified",
        "method_accepted",
        "positive_label_permitted",
        "negative_label_permitted",
        "training_authorized",
        "model_ready",
        "final_merge_permitted",
        "2023_calibration_values_read_permitted",
        "2024_comparison_values_read_permitted",
        "2025_final_values_read_permitted",
    )
    require(all(p[k] is False for k in closed), "Preparation cannot open scientific gates")
    require(p["all_source_rows_retained"] is True, "Preserve complete source frame")
    require(p["daily_observation_status"] == "unknown", "Unknown observation")
    g, t, u = p["geometry_diagnostics"], p["time_diagnostics"], p["U_domain_diagnostic"]
    require(
        g["projection"] == "EPSG:6933" and g["radii_projection_plane_m"] == [0, 250, 1000],
        "Bounded exploratory radii",
    )
    require(
        g["circle_quad_segs"] == 64 and g["positive_area_intersections_for_nonzero_radius"] is True,
        "Declared polygon approximation",
    )
    require(
        all(
            g[k] is False
            for k in (
                "radii_are_measured_location_error_bounds",
                "all_intersected_cells_are_positive",
                "force_nearest_cell",
            )
        ),
        "Geometry alternatives are not labels",
    )
    require(
        t["day_shifts"] == [-1, 0, 1] and t["keep_both_clock_hypotheses"] is True,
        "Preserve exploratory time alternatives",
    )
    require(
        all(
            t[k] is False
            for k in (
                "shifts_are_measured_detection_delays",
                "source_clock_is_first_satellite_detection",
                "select_clock_using_satellite_match",
            )
        ),
        "No inferred detection time",
    )
    require(
        t["start_T_utc"] == "2018-01-01T00:00:00+00:00"
        and t["target_endpoint_strictly_before"] == "2023-01-01T00:00:00+00:00",
        "Existing fit boundary",
    )
    require(
        u["review_slice"] == "retained_water_scope_cell_has_positive_area_in_Mersin",
        "Geographic review slice only",
    )
    require(
        all(
            u[k] is False
            for k in (
                "slice_is_accepted_training_population",
                "new_sampling_permitted",
                "drop_overlaps_with_source_keys",
                "unknown_is_negative",
                "geographic_overlap_proves_shared_class_conditionals",
            )
        ),
        "No U relabeling or outcome-based edits",
    )
    mix = p["mixture_requirements"]
    require(
        all(
            mix[k] is False
            for k in (
                "source_L_positive_enrichment_verified",
                "shared_class_conditionals_verified",
                "semantic_identifiability_verified",
                "independent_evaluation_supported",
            )
        ),
        "Unresolved mixture assumptions",
    )
    require(
        all(mix[k] is None for k in ("alpha", "beta", "label_noise_fraction")), "No rate estimates"
    )
    dep = p["dependency_diagnostic"]
    require(
        dep["basis"] == "shared_cell_day_in_1km_and_plus_minus_one_day_hypotheses"
        and dep["source_rows_are_not_merged"] is True
        and dep["physical_fire_identity_verified"] is False
        and dep["fold_assignment_performed"] is False,
        "Hypothesis dependency is not event identity or an actual split",
    )


def shifted_windows(start, shifts):
    stamp = datetime.fromisoformat(start)
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "UTC metadata")
    require(stamp.time().replace(tzinfo=None) == datetime.min.time(), "Midnight prediction")
    require(2018 <= stamp.year <= 2022, "Fit-role source window only")
    return [
        {
            "day_shift": shift,
            "window_start_utc": (stamp + timedelta(days=shift)).isoformat(),
            "inside_fit": datetime(2018, 1, 1, tzinfo=UTC) <= stamp + timedelta(days=shift)
            and stamp + timedelta(days=shift + 1) < datetime(2023, 1, 1, tzinfo=UTC),
        }
        for shift in shifts
    ]


def spatial_options(point, grid, radii):
    result = []
    for radius in radii:
        shape = point if radius == 0 else point.buffer(radius, quad_segs=64)
        nearby = grid.iloc[grid.sindex.query(shape, predicate="intersects")]
        if radius:
            nearby = nearby.loc[nearby.geometry.intersection(shape).area.gt(0)]
        result.append(
            {"radius_projection_plane_m": radius, "grid_ids": sorted(nearby.grid_id.tolist())}
        )
    return result


def domain_slice(u_rows, domain):
    keys = set()
    selected = []
    for row in u_rows:
        stamp = datetime.fromisoformat(row["prediction_timestamp_utc"])
        require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "U UTC metadata")
        require(
            datetime(2018, 1, 1, tzinfo=UTC) <= stamp
            and stamp + timedelta(days=1) < datetime(2023, 1, 1, tzinfo=UTC),
            "Fit U keys before other context",
        )
        require(stamp.time().replace(tzinfo=None) == datetime.min.time(), "U midnight prediction")
        require(
            row["target"] in (None, "") and row["daily_observation_status"] == "unknown",
            "U remains unknown, never negative",
        )
        key = (row["grid_id"], stamp.isoformat())
        require(key not in keys, "Unique frozen U key")
        keys.add(key)
        if row["grid_id"] in domain:
            selected.append(dict(row))
    return selected


def cell_multiplicity(cases, radii):
    result = {}
    for radius in radii:
        counts = Counter(
            len(
                next(
                    s["grid_ids"]
                    for s in row["spatial_alternatives"]
                    if s["radius_projection_plane_m"] == radius
                )
            )
            for row in cases
            if row["diagnostic_focus"]
        )
        result[str(radius)] = {str(n): count for n, count in sorted(counts.items())}
    return result


def plausible_key_dependencies(cases):
    """Keep possible shared-key dependencies for future split design, not fire merging."""
    focus = [r for r in cases if r["diagnostic_focus"]]
    parents = {r["archive_row"]: r["archive_row"] for r in focus}

    def root(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    owner = {}
    for row in focus:
        cells = next(
            x["grid_ids"]
            for x in row["spatial_alternatives"]
            if x["radius_projection_plane_m"] == 1000
        )
        for time in row["temporal_alternatives"]:
            if not time["inside_fit"]:
                continue
            for cell in cells:
                key = (cell, time["window_start_utc"])
                if key in owner:
                    parents[root(row["archive_row"])] = root(owner[key])
                else:
                    owner[key] = row["archive_row"]
    groups = defaultdict(list)
    for key in sorted(parents):
        groups[root(key)].append(key)
    blocks = sorted(groups.values())
    return {
        "all_hypothesis_components": len(blocks),
        "multiple_source_record_blocks": [x for x in blocks if len(x) > 1],
        "source_rows_in_multiple_record_blocks": sum(len(x) for x in blocks if len(x) > 1),
        "components_are_independent_physical_fires": False,
        "source_records_merged_or_deleted": False,
        "fold_assignment_performed": False,
    }


def main():
    require(digest(PARENT) == PARENT_SHA, "Frozen reviewed source cohort")
    parent = json.loads(PARENT.read_bytes())
    pins = {ROOT / k: h for k, h in parent["input_sha256"].items()}
    pins.update({PARENT: PARENT_SHA, WATER: WATER_SHA, POLICY: digest(POLICY)})
    require(
        all(digest(p) == h for p, h in pins.items()), "Source, scope, prior L/U and decision pins"
    )
    policy = json.loads(POLICY.read_bytes())
    validate_policy(policy)
    with WATER.open(encoding="utf-8-sig", newline="") as f:
        scope = list(csv.DictReader(f))
    retained = {x["grid_id"] for x in scope if x["water_scope_included"] == "True"}
    require(len(retained) == 2889 and len(scope) == 2899, "Same retained water scope")
    grid = gpd.read_file(GRID).to_crs(6933)
    grid = grid.loc[grid.grid_id.isin(retained)].reset_index(drop=True)
    require(grid.grid_id.is_unique and len(grid) == 2889, "Retained grid keys")
    province = gpd.read_file(PROVINCES).to_crs(6933)
    mersin = province.loc[province.GAUL1_CODE.astype(str).eq("3160"), "geometry"].iloc[0]
    overlap = grid.geometry.intersection(mersin).area
    domain = set(grid.loc[overlap.gt(0), "grid_id"])
    with U.open(encoding="utf-8-sig", newline="") as f:
        u_rows = list(csv.DictReader(f))
    require(len(u_rows) == 2048, "Same frozen U sample")
    sliced = domain_slice(u_rows, domain)
    all_u_keys = {(x["grid_id"], x["prediction_timestamp_utc"]) for x in u_rows}
    with ZipFile(ARCHIVE) as archive:
        geo = {x["event_id"]: x for x in filtered_rows(archive, GEO)}
    require(set(geo) == {x["archive_row"] for x in parent["rows"]}, "All 424 source keys retained")
    project = Transformer.from_crs(4326, 6933, always_xy=True)
    cases, variants = [], defaultdict(set)
    outside_fit = Counter()
    for row in parent["rows"]:
        focus = (
            row["metadata_transportable_under_center_and_clock_hypotheses"]
            and not row["researcher_retained_outside_L"]
        )
        case = {
            **row,
            "diagnostic_focus": focus,
            "spatial_alternatives": [],
            "temporal_alternatives": [],
        }
        if focus:
            raw = geo[row["archive_row"]]
            point = Point(*project.transform(float(raw["longitude"]), float(raw["latitude"])))
            spaces = spatial_options(
                point, grid, policy["geometry_diagnostics"]["radii_projection_plane_m"]
            )
            times = shifted_windows(
                row["conditional_target_window_starts"][0], policy["time_diagnostics"]["day_shifts"]
            )
            case["spatial_alternatives"], case["temporal_alternatives"] = spaces, times
            for space in spaces:
                for time in times:
                    key = (space["radius_projection_plane_m"], time["day_shift"])
                    if not time["inside_fit"]:
                        outside_fit[key] += 1
                    variants[key].update(
                        (cell, time["window_start_utc"])
                        for cell in space["grid_ids"]
                        if time["inside_fit"]
                    )
        cases.append(case)
    require(
        len(cases) == 424 and sum(x["diagnostic_focus"] for x in cases) == 380,
        "Fixed focus without source deletion",
    )
    summary = []
    for (radius, shift), keys in sorted(variants.items()):
        summary.append(
            {
                "radius_projection_plane_m": radius,
                "day_shift": shift,
                "distinct_in_fit_hypothesis_keys": len(keys),
                "hypothesis_keys_in_Mersin_domain": sum(k[0] in domain for k in keys),
                "overlaps_with_unchanged_U_keys": len(keys & all_u_keys),
                "outside_fit_source_hypotheses_retained": outside_fit[(radius, shift)],
            }
        )
    distribution = cell_multiplicity(
        cases, policy["geometry_diagnostics"]["radii_projection_plane_m"]
    )
    report = {
        "status": "source_conditioned_protocol_diagnostics_complete_not_method_acceptance",
        "decision": policy,
        "source_rows_retained": len(cases),
        "diagnostic_focus_rows": 380,
        "source_rows_outside_focus_retained": 44,
        "cell_count_distribution_by_radius": distribution,
        "scenario_key_summary": summary,
        "plausible_key_dependencies": plausible_key_dependencies(cases),
        "U_original_rows_preserved": len(u_rows),
        "U_Mersin_geographic_review_slice_rows": len(sliced),
        "retained_cells": len(retained),
        "Mersin_positive_area_cells": len(domain),
        "U_slice_is_representative_positive_or_negative_sample": False,
        "geographic_conditioning_validates_mixture": False,
        "calendar_counts_are_shared_class_conditional_tests": False,
        "calendar_counts": {
            "source_focus_rows_by_conditional_year_month": dict(
                sorted(
                    Counter(
                        x["conditional_target_window_starts"][0][:7]
                        for x in cases
                        if x["diagnostic_focus"]
                    ).items()
                )
            ),
            "source_distinct_center_keys_by_year_month": dict(
                sorted(Counter(day[:7] for _, day in variants[(0, 0)]).items())
            ),
            "U_Mersin_slice_by_year_month": dict(
                sorted(Counter(x["prediction_timestamp_utc"][:7] for x in sliced).items())
            ),
        },
        "radii_or_shifts_estimate_source_error": False,
        "cases": cases,
        "unresolved_requirements": [
            "source_record_identity_and_coordinate_role",
            "source_to_first_detection_time_relation",
            "local_forest_shrub_context",
            "positive_enrichment_and_shared_class_conditionals",
            "noise_rates_semantic_identifiability_and_independent_evaluation",
        ],
        "new_L_memberships": 0,
        "binary_labels_created": 0,
        "rates_estimated": False,
        "model_trained": False,
        "features_joined": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    out = (
        BASE
        / "source_conditioned_pu_protocol_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    slice_path = out / "U_Mersin_geographic_review_slice.csv"
    with slice_path.open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(u_rows[0]))
        writer.writeheader()
        writer.writerows(sliced)
    report["artifact_sha256"] = {slice_path.name: digest(slice_path)}
    path = out / "readback.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Saved protocol readback")
    require(all(digest(p) == h for p, h in pins.items()), "Inputs unchanged at closure")
    with slice_path.open(encoding="utf-8", newline="") as f:
        require(
            list(csv.DictReader(f)) == sliced,
            "U review slice exactly preserves original row values",
        )
    verified = {
        "readback_sha256": digest(path),
        "JSON_roundtrip_equal": True,
        "input_pins_unchanged": True,
        "U_slice_roundtrip_equal": True,
        "completion_is_scientific_acceptance": False,
    }
    (out / "verification.json").write_text(json.dumps(verified, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "cell_count_distribution_by_radius",
                    "scenario_key_summary",
                    "U_Mersin_geographic_review_slice_rows",
                    "Mersin_positive_area_cells",
                )
            }
        )
    )
    print("PASS protocol_prepared_offline_diagnostics_only; no L, target, rates or training")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
