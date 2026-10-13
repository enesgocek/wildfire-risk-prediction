"""Snapshot rejects altered state, unsafe filenames and writes no production bytes."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v6_geo_snapshot", ROOT / "scripts/cloud/collect_gcp_v6_geolocation_snapshot.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def home(tmp_path, monkeypatch):
    work = tmp_path / "wildfire-gcp-production-v1"
    work.mkdir()
    for folder, filename, constant in (
        ("wildfire-gcp-production-package", "production_manifest.json", "SCOPE"),
        ("wildfire-gcp-acceleration-package", "acceleration_manifest.json", "CONTROLLER"),
    ):
        package = tmp_path / folder
        package.mkdir()
        payload = b"public package member"
        (package / "public.py").write_bytes(payload)
        manifest = json.dumps({"files": {"public.py": module.sha(payload)}}).encode()
        (package / filename).write_bytes(manifest)
        monkeypatch.setattr(module, constant, module.sha(manifest))
    wrapper = b"public synthetic wrapper"
    (tmp_path / "run_gcp_source_aware_continuation_v6.py").write_bytes(wrapper)
    monkeypatch.setattr(module, "WRAPPER_SHA", module.sha(wrapper))
    registry = b'{"public":"registry"}'
    (tmp_path / "source_blocks.json").write_bytes(registry)
    monkeypatch.setattr(module, "REGISTRY", module.sha(registry))
    state = {
        "status": "failed_checkpoints_retained",
        "failed_month": "2018-06",
        "failed_phase": "pair_publication",
        "continuation_wrapper_sha256": module.WRAPPER_SHA,
        "queue_manifest_sha256": module.SCOPE,
        "controller_manifest_sha256": module.CONTROLLER,
        "source_block_registry_sha256": module.REGISTRY,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "full_training_complete": False,
        "existing_months": [
            f"{y}-{m:02d}"
            for y in range(2018, 2024)
            for m in range(1, 13)
            if "2018-07" <= f"{y}-{m:02d}" <= "2023-11"
        ],
    }
    raw = json.dumps(state).encode()
    monkeypatch.setattr(module, "FINAL_SHA", module.sha(raw))
    for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json"):
        (work / name).write_bytes(raw)
    pairs = []
    for identity in module.FOCUS:
        key = identity.split(":")[1]
        fire = f"VJ114IMG.A{key}.002.2024001000000.nc"
        geo = f"VJ103IMG.A{key}.002.2019001000000.nc"
        declared = f"VJ103IMG.A{key}.002.2019002000000.nc"
        stem = "l2_sample_" + identity.replace(":", "_")
        sources = [
            {"role": role, "filename": name, "bytes": 11}
            for role, name in (("fire", fire), ("geolocation", geo))
        ]
        pairs.append({"sample_id": identity, "stem": stem, "sources": sources})
        root = work / "months/2018-06/accelerated_run/tasks" / module.sha(identity.encode())
        raw_root = root / "summer/raw" / stem
        raw_root.mkdir(parents=True)
        for name in (fire, geo):
            (raw_root / name).write_bytes(b"RAW_CONTENT")
        (root / "continuation_failure.json").write_text(
            json.dumps(
                {
                    "sample_id": identity,
                    "child_kind": "pair",
                    "error_type": "ValueError",
                    "guard": "Not the actual geolocation input",
                    "declared_geolocation_filenames": [declared],
                    "selected_geolocation_filename": geo,
                    "unrelated_private_field": "must not be exported",
                }
            ),
            encoding="utf-8",
        )
    meta = work / "months/2018-06/metadata"
    meta.mkdir()
    (meta / "month.json").write_text(
        json.dumps({"month": "2018-06", "negative_label_permitted": False, "pairs": pairs}),
        encoding="utf-8",
    )
    return tmp_path


def failure_path(home):
    return (
        home
        / "wildfire-gcp-production-v1/months/2018-06/accelerated_run/tasks"
        / module.sha(module.FOCUS[0].encode())
        / "continuation_failure.json"
    )


def test_snapshot_is_offline_sanitized_and_does_not_read_raw(home, monkeypatch):
    before = {p: module.sha(p.read_bytes()) for p in home.rglob("*") if p.is_file()}
    original = Path.read_bytes

    def guarded(path):
        assert "raw" not in path.parts and ".config" not in path.parts
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    result = module.snapshot(home)
    assert len(result["failures"]) == 6 and result["protected_files_unchanged"]
    assert result["network_requests"] == result["production_writes"] == 0
    assert not result["credentials_read"] and not result["raw_source_contents_read"]
    assert "must not be exported" not in json.dumps(result)
    monkeypatch.setattr(Path, "read_bytes", original)
    assert before == {p: module.sha(p.read_bytes()) for p in home.rglob("*") if p.is_file()}


def test_modified_final_is_rejected(home):
    (home / "wildfire-gcp-production-v1/progress.json").write_text("{}")
    with pytest.raises(ValueError, match="Exact reviewed final"):
        module.snapshot(home)


def test_modified_package_member_is_rejected(home):
    (home / "wildfire-gcp-production-package/public.py").write_text("changed")
    with pytest.raises(ValueError, match="Package member identity"):
        module.snapshot(home)


def test_external_text_cannot_be_exported_as_filename(home):
    path = failure_path(home)
    value = json.loads(path.read_bytes())
    value["declared_geolocation_filenames"] = ["https://example.invalid/?token=hidden"]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Public lineage filename"):
        module.snapshot(home)


def test_unavailable_header_is_explicit(home):
    path = failure_path(home)
    value = json.loads(path.read_bytes())
    value["header_detail"] = "UNAVAILABLE"
    value.pop("declared_geolocation_filenames")
    path.write_text(json.dumps(value))
    result = module.snapshot(home)
    assert result["failures"][0]["header_detail"] == "UNAVAILABLE"
    assert "declared_geolocation_filenames" not in result["failures"][0]


def test_raw_size_mismatch_is_reported_without_reading_contents(home):
    raw = next((home / "wildfire-gcp-production-v1").rglob("*.nc"))
    raw.write_bytes(b"short")
    result = module.snapshot(home)
    stats = [s for row in result["failures"] for s in row["raw_source_stats"]]
    assert any(s["actual_bytes"] != s["expected_bytes"] for s in stats)


def test_path_traversal_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Source boundary"):
        module.boundary(tmp_path.parent / "outside.json", tmp_path)


def test_evidence_change_during_snapshot_is_rejected(home, monkeypatch):
    path = failure_path(home)
    original = Path.read_bytes
    count = 0

    def changed(file):
        nonlocal count
        raw = original(file)
        if file == path:
            count += 1
            if count == 1:
                file.write_bytes(raw + b" ")
        return raw

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="Protected evidence changed"):
        module.snapshot(home)
