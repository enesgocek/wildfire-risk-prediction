"""Hash-bound daily feature parts for an unlabelled training pilot; no fitting or downloads."""

import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction import feature_join as join

VERSION = "training_feature_partition_pilot_v1"


def provenance_columns():
    return (
        join.KEYS
        + join.WEATHER_QA
        + [
            "weather_source_last_timestamp_utc",
            "weather_available_at",
            "weather_source_collection",
            "weather_source_window_start_utc",
            "weather_source_window_end_exclusive_utc",
            "weather_rain_interval_end_utc",
        ]
        + ["static_" + f for f in join.STATIC_QA]
        + [f"vegetation_{w}d_{f}" for w in join.WINDOWS for f in join.VEGETATION_QA]
        + ["usage", "operational_eligible", "habitat_eligibility_decided", "join_version"]
    )


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_identity(grid_ids):
    ids = sorted(grid_ids)
    join.require(
        ids and all(isinstance(g, str) and g.strip() for g in ids) and len(ids) == len(set(ids)),
        "Unique grid inventory",
    )
    return ids, digest(json.dumps(ids, ensure_ascii=False).encode("utf-8"))


def check_day(features, provenance, grid_ids, day):
    target = join.training_day(day)
    ids, _ = grid_identity(grid_ids)
    join.require(features.columns.tolist() == join.KEYS + join.feature_names(), "Feature allowlist")
    join.require(provenance.columns.tolist() == provenance_columns(), "Provenance allowlist")
    for name, frame in [("features", features), ("provenance", provenance)]:
        join.require(frame.columns.is_unique and set(join.KEYS) <= set(frame), "Unique schema")
        join.grid_rows(frame, ids, name)
        join.require(
            join.utc_times(frame.prediction_timestamp_utc).eq(target).all(),
            "Partition day mismatch",
        )
    join.require(
        all(
            pd.api.types.is_numeric_dtype(features[f])
            and not pd.api.types.is_bool_dtype(features[f])
            for f in join.feature_names()
        ),
        "Numeric feature values",
    )
    values = features[join.feature_names()].to_numpy(float)
    join.require((np.isfinite(values) | np.isnan(values)).all(), "Infinite feature value")
    for name in ["operational_eligible", "habitat_eligibility_decided"]:
        join.boolean(provenance[name], name)
        join.require(not provenance[name].any(), "Pilot acceptance state changed")
    join.require(
        provenance.usage.eq("retrospective_candidate_only").all()
        and provenance.join_version.eq(join.VERSION).all(),
        "Retrospective join identity",
    )
    # Align both tables by identities, never by their incoming row order.
    return tuple(f.set_index("grid_id").loc[ids].reset_index() for f in (features, provenance))


def write_pilot(folder, days, grid_ids):
    """Write one day at a time; publish manifest only after every part passes readback.

    The destination must be new. On failure, incomplete parts remain without a manifest.
    This pilot API does not grant label, training or full-calendar acceptance.
    """
    ids, grid_sha = grid_identity(grid_ids)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    entries, seen, qa_columns = [], set(), None
    for day, features, provenance in days:
        join.training_day(day)
        join.require(day not in seen, "Duplicate partition day")
        seen.add(day)
        features, provenance = check_day(features, provenance, ids, day)
        if qa_columns is None:
            qa_columns = provenance.columns.tolist()
        join.require(provenance.columns.tolist() == qa_columns, "Provenance schema drift")
        month = folder / day[:7]
        month.mkdir(exist_ok=True)
        entry = {"day": day, "rows": len(ids), "artifacts": {}}
        for kind, frame in [("features", features), ("provenance", provenance)]:
            name = f"{day[:7]}/{day}_{kind}.csv"
            path = folder / name
            frame.to_csv(path, index=False)
            data = path.read_bytes()
            saved = parse_csv(data)
            pd.testing.assert_frame_equal(frame, saved, check_dtype=False, check_exact=True)
            entry["artifacts"][kind] = {"path": name, "sha256": digest(data), "bytes": len(data)}
        entry["missing_by_feature"] = {
            f: int(features[f].isna().sum()) for f in join.feature_names()
        }
        entries.append(entry)
    join.require(entries, "Empty partition pilot")
    manifest = {
        "version": VERSION,
        "scope": "sparse_training_pilot",
        "split": "train",
        "model_ready": False,
        "labels_created": False,
        "final_test_accessed": False,
        "historical_availability_verified": False,
        "qa_columns_are_model_inputs": False,
        "grid_count": len(ids),
        "grid_identity_sha256": grid_sha,
        "feature_columns": join.KEYS + join.feature_names(),
        "provenance_columns": qa_columns,
        "rows": sum(e["rows"] for e in entries),
        "days": sorted(entries, key=lambda e: e["day"]),
    }
    data = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    (folder / "manifest.json").write_bytes(data)
    return digest(data)


def parse_csv(data):
    return pd.read_csv(
        io.BytesIO(data),
        dtype={k: str for k in join.KEYS},
        keep_default_na=False,
        na_values=[""],
        float_precision="round_trip",
    )


def iter_pilot(folder, *, expected_manifest_sha256, grid_ids):
    """Yield one checked training day; external manifest hash is required, QA stays separate.

    Hash checks detect change relative to that supplied identity, not source truth or OS access.
    Only this pilot's generated paths are read. Scope/day checks precede CSV access.
    """
    folder = Path(folder).resolve()
    ids, grid_sha = grid_identity(grid_ids)
    manifest_path = folder / "manifest.json"
    join.require(not manifest_path.is_symlink(), "Manifest symlink")
    data = manifest_path.read_bytes()
    join.require(
        re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256)
        and digest(data) == expected_manifest_sha256,
        "Manifest identity mismatch",
    )
    manifest = json.loads(data)
    join.require(
        manifest["version"] == VERSION
        and manifest["scope"] == "sparse_training_pilot"
        and manifest["split"] == "train"
        and all(
            manifest[f] is False
            for f in [
                "model_ready",
                "labels_created",
                "final_test_accessed",
                "historical_availability_verified",
                "qa_columns_are_model_inputs",
            ]
        ),
        "Pilot scope/acceptance changed",
    )
    join.require(
        manifest["grid_count"] == len(ids)
        and manifest["grid_identity_sha256"] == grid_sha
        and manifest["feature_columns"] == join.KEYS + join.feature_names(),
        "Grid/schema identity mismatch",
    )
    entries = manifest["days"]
    days = [entry["day"] for entry in entries]
    join.require(days and days == sorted(set(days)), "Ordered unique partition days")
    for day in days:
        join.training_day(day)  # Reject every held-out day before reading any data part.
    join.require(
        manifest["rows"] == len(days) * len(ids)
        and all(entry["rows"] == len(ids) for entry in entries),
        "Row inventory mismatch",
    )
    for entry in entries:
        day, tables = entry["day"], []
        join.require(set(entry["artifacts"]) == {"features", "provenance"}, "Artifact kinds")
        for kind in ["features", "provenance"]:
            artifact = entry["artifacts"][kind]
            name = f"{day[:7]}/{day}_{kind}.csv"
            join.require(artifact["path"] == name, "Unexpected partition path")
            path = folder / name
            join.require(
                not path.is_symlink() and path.resolve().is_relative_to(folder), "Partition path"
            )
            data = path.read_bytes()
            join.require(
                len(data) == artifact["bytes"] and digest(data) == artifact["sha256"],
                "Partition content mismatch",
            )
            frame = parse_csv(data)
            columns = "feature_columns" if kind == "features" else "provenance_columns"
            join.require(frame.columns.tolist() == manifest[columns], "Part schema")
            tables.append(frame)
        features, provenance = check_day(*tables, ids, day)
        join.require(
            entry["missing_by_feature"]
            == {f: int(features[f].isna().sum()) for f in join.feature_names()},
            "Missingness inventory mismatch",
        )
        yield day, features, provenance
