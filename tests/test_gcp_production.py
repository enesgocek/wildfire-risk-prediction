"""Full-period production guardrails, frozen science and indexed Drive; no cloud access."""

import copy
import datetime as dt
import importlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
support = importlib.import_module("gcp_production_support")
runner = importlib.import_module("run_gcp_production")
drive = importlib.import_module("production_drive_store")


@pytest.fixture(scope="module")
def legacy():
    path = ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("summer/manifest.json"))
        pair = manifest["pairs"][0]
        source = pair["sources"][0]
        metadata = json.loads(archive.read(pair["metadata"][source["role"]]))
    frame = pd.read_csv(
        ROOT / "outputs/reports/observation_coverage/l2_training_catalogue_granules.csv",
        dtype={"pair_key": str},
    )
    row = frame.loc[frame.filename.eq(source["filename"])].iloc[0]
    return pair, source, row, metadata


def test_exact_umm_size_and_frozen_stem(legacy):
    pair, source, row, metadata = legacy
    assert support.source_size(row, metadata) == source["bytes"]
    assert pair["stem"] == "l2_sample_" + ("N20_" if pair["sensor"] == "N20" else "") + pair["key"]


@pytest.mark.parametrize(
    "mutation", ["product", "version", "interval", "url", "size", "identifiers"]
)
def test_bad_metadata_cannot_start_a_source_download(legacy, mutation):
    _, _, row, original = legacy
    meta = copy.deepcopy(original)
    if mutation == "product":
        meta["CollectionReference"]["ShortName"] = "OTHER"
    elif mutation == "version":
        meta["CollectionReference"]["Version"] = "1"
    elif mutation == "interval":
        meta["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"] = "2025-01-01T00:00:00Z"
    elif mutation == "url":
        meta["RelatedUrls"] = []
    elif mutation == "size":
        meta["DataGranule"]["ArchiveAndDistributionInformation"][0]["SizeInBytes"] = 5
    else:
        meta["DataGranule"]["Identifiers"] = []
    with pytest.raises(ValueError):
        support.source_size(row, meta)


@pytest.mark.parametrize(
    "url", ["http://data.lpdaac.earthdatacloud.nasa.gov/file.nc", "https://evil.test/file.nc"]
)
def test_unapproved_data_hosts_rejected_before_auth(legacy, url):
    _, _, row, meta = legacy
    row = row.copy()
    row.data_url = url
    with pytest.raises(ValueError, match="URL"):
        support.source_size(row, meta)


def test_deadline_absolute_timezone_and_trial_guard():
    now = dt.datetime(2026, 10, 6, tzinfo=dt.UTC)
    assert runner.deadline_seconds("2026-10-06T08:00:00Z", now) == 7.75 * 3600
    for value in ("2026-10-06T01:00:00", "2026-10-06T00:10:00Z", "2026-10-07T01:00:00Z"):
        with pytest.raises(ValueError):
            runner.deadline_seconds(value, now)
    with pytest.raises(ValueError, match="Trial"):
        runner.deadline_seconds("2026-10-24T08:00:00Z", dt.datetime(2026, 10, 24, tzinfo=dt.UTC))


def test_environment_never_reuses_tokens_or_python_injection(monkeypatch):
    monkeypatch.setenv("EARTHDATA_TOKEN", "test_only")
    monkeypatch.setenv("PYTHONPATH", "untrusted")
    env = runner.environment()
    assert "EARTHDATA_TOKEN" not in env and "PYTHONPATH" not in env
    assert env["OMP_NUM_THREADS"] == "1"
    auth = runner.environment({"username": "example", "password": "dummy"})
    assert auth["EARTHDATA_USERNAME"] == "example"
    assert auth["EARTHDATA_PASSWORD"] == "dummy"


def test_secret_pipe_is_bounded_and_not_a_disk_file():
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b'{"username":"example","password":"dummy"}')
    os.close(write_fd)
    assert runner.read_auth(read_fd) == {"username": "example", "password": "dummy"}
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b'{"token":"dummy"}')
    os.close(write_fd)
    with pytest.raises(ValueError, match="schema"):
        runner.read_auth(read_fd)


def test_cleanup_never_removes_base_or_outside(tmp_path):
    base, outside = tmp_path / "owned", tmp_path / "other"
    base.mkdir()
    outside.mkdir()
    for target in (base, outside):
        with pytest.raises(ValueError):
            support.owned_remove(target, base)
    sub = base / "task"
    sub.mkdir()
    (sub / "data").write_text("verified scratch")
    support.owned_remove(sub, base)
    assert base.exists() and outside.exists() and not sub.exists()


def test_resume_does_not_overwrite_existing_metadata(tmp_path):
    core, meta, root = tmp_path / "core", tmp_path / "metadata", tmp_path / "root"
    core.mkdir()
    meta.mkdir()
    (meta / "G123-TEST.json").write_text('{"value":1}')
    pairs = [
        {
            "metadata": {
                "fire": "production_metadata/G123-TEST.json",
                "geolocation": "production_metadata/G123-TEST.json",
            }
        }
    ]
    runner.ensure_root(root, core, meta, pairs)
    (meta / "G123-TEST.json").write_text('{"value":2}')
    with pytest.raises(ValueError, match="changed"):
        runner.ensure_root(root, core, meta, pairs)


def test_partial_source_is_redownloaded_and_valid_length_is_kept(tmp_path):
    pair = {
        "sources": [{"filename": "valid.nc", "bytes": 4}, {"filename": "partial.nc", "bytes": 4}]
    }
    (tmp_path / "valid.nc").write_bytes(b"data")
    (tmp_path / "partial.nc").write_bytes(b"x")
    runner.discard_partial_sources(tmp_path, pair)
    assert (tmp_path / "valid.nc").read_bytes() == b"data"
    assert not (tmp_path / "partial.nc").exists()
    with pytest.raises(ValueError, match="basename"):
        runner.discard_partial_sources(
            tmp_path, {"sources": [{"filename": "../outside", "bytes": 4}]}
        )


def test_arbitrary_external_errors_never_enter_public_logs():
    assert runner.safe_guard(ValueError("Earthdata login failed")) == "Earthdata login failed"
    assert runner.safe_guard(ValueError("token=secret URL")) == "No external error text logged"


def test_changed_science_manifest_is_rejected_before_import(tmp_path):
    (tmp_path / "summer").mkdir()
    (tmp_path / "summer/manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="manifest changed"):
        support.science(tmp_path)


@pytest.fixture
def monthly_fixture(tmp_path, legacy):
    pair = legacy[0]
    catalogue = pd.read_csv(
        ROOT / "outputs/reports/observation_coverage/l2_training_catalogue_pairs.csv",
        dtype={"pair_key": str},
    )
    sources = pd.read_csv(
        ROOT / "outputs/reports/observation_coverage/l2_training_catalogue_granules.csv",
        dtype={"pair_key": str},
    )
    rows = sources.loc[sources.sensor.eq(pair["sensor"]) & sources.pair_key.eq(pair["key"])].copy()
    rows["day"] = rows.start_utc.str[:10]
    with zipfile.ZipFile(ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip") as archive:
        metadata = {
            row.concept_id: json.loads(archive.read(pair["metadata"][row.role]))
            for row in rows.itertuples()
        }
    destination = tmp_path / "metadata"
    plan = support.build_month(
        "2023-07",
        rows,
        catalogue,
        tmp_path,
        destination,
        fetch=lambda concept, cache: metadata[concept],
    )
    return rows, catalogue, destination, plan


def test_real_month_metadata_canonical_sha_and_roundtrip(tmp_path, monthly_fixture):
    rows, catalogue, destination, plan = monthly_fixture
    payload = tmp_path / "month.zip"
    support.pack_flat(destination, support.month_names(rows), payload)
    assert support.validate_month(payload, "2023-07", rows, catalogue, tmp_path / "fresh") == plan
    assert len(plan["days"]) == 31 and plan["pairs"][0]["stem"].endswith("2023197.0018")
    for source in plan["pairs"][0]["sources"]:
        assert source["provider"] == ("LPCLOUD" if source["role"] == "fire" else "LAADS")


@pytest.mark.parametrize("mutation", ["calendar", "pair_count", "labels", "gaps", "metadata_sha"])
def test_month_corruption_cannot_enter_science(tmp_path, monthly_fixture, mutation):
    rows, catalogue, destination, plan = monthly_fixture
    if mutation == "calendar":
        plan["days"].pop()
    elif mutation == "pair_count":
        plan["pairs"].clear()
    elif mutation == "labels":
        plan["negative_label_permitted"] = True
    elif mutation == "gaps":
        plan["unpaired_catalogue_records"].append({"invented": True})
    else:
        plan["pairs"][0]["sources"][0]["metadata_sha256"] = "0" * 64
    support.atomic_json(destination / "month.json", plan)
    payload = tmp_path / "month.zip"
    support.pack_flat(destination, support.month_names(rows), payload)
    with pytest.raises(ValueError):
        support.validate_month(payload, "2023-07", rows, catalogue)


class IndexedAPI:
    def __init__(self):
        self.files, self.data, self.queries = [], {}, []

    def listing(self, query):
        self.queries.append(query)
        job = re.search(r"value='([a-f0-9]{64})'", query)[1]
        name = re.search(r"and name = '([^']+)'", query)
        return [
            r
            for r in self.files
            if r["appProperties"]["job"] == job and (not name or r["name"] == name[1])
        ]

    def create_file(self, meta, data):
        identity = "object_" + str(len(self.files))
        self.files.append({**meta, "id": identity, "size": str(len(data))})
        self.data[identity] = data
        return identity

    def request(self, path):
        return self.data[path.split("/")[2].split("?")[0]]


def key(job="a", payload="b"):
    return "jobs/" + job * 64 + "/" + "c" * 64 + "/" + payload * 64 + ".zip"


def test_indexed_reads_quota_and_immutable_uploads():
    api = IndexedAPI()
    backend = drive.ProductionDriveStore(api, "folder_1234567890")
    backend.create(key(), b"science")
    backend.create(key(payload="d"), b"other")
    assert backend.used_bytes("jobs/" + "a" * 64) == 12
    full_listings = sum("and name" not in q for q in api.queries)
    for _ in range(10):
        assert backend.get(key()) == b"science"
        assert backend.used_bytes("jobs/" + "a" * 64) == 12
    assert sum("and name" not in q for q in api.queries) == full_listings == 1
    backend.create(key(), b"science")
    assert len(api.files) == 2 and backend.used_bytes("jobs/" + "a" * 64) == 12
    with pytest.raises(ValueError, match="collision"):
        backend.create(key(), b"changed")


def test_duplicates_and_role_mismatch_still_fail_closed():
    api = IndexedAPI()
    backend = drive.ProductionDriveStore(api, "folder_1234567890")
    backend.create(key(), b"science")
    api.files.append({**api.files[0], "id": "different"})
    with pytest.raises(ValueError, match="Duplicate"):
        backend.get(key())
    api.files.pop()
    api.files[0]["mimeType"] = "application/json"
    with pytest.raises(ValueError, match="role"):
        backend.get(key())


def test_other_jobs_do_not_trigger_folder_wide_payload_lookup():
    api = IndexedAPI()
    backend = drive.ProductionDriveStore(api, "folder_1234567890")
    backend.create(key("d"), b"other")
    assert backend.get(key()) is None
    assert backend.used_bytes("jobs/" + "a" * 64) == 0
    assert all("appProperties has" in q for q in api.queries)
