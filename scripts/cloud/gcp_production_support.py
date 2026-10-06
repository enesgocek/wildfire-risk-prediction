"""Full-training scope, immutable monthly metadata and frozen native science support."""

import hashlib
import importlib.util
import json
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pandas as pd
from verified_job_store import require

SUMMER_SHA = "0a90b93be0ed31fa468b6ecef61851612bcd255e34caf3ccdb6adf2d6d425f7e"
COMPACT_SHA = "f09e73837732160a65cc059c382c2ed85a95de0985aa470c1ec5789f6dc17b54"
SUMMER_MANIFEST_SHA = "fc394318dbe2c7c220c1bb0d09d8da915941f5313eb871dfd83c64706c97b77a"
DATA_HOSTS = {"data.lpdaac.earthdatacloud.nasa.gov", "data.laadsdaac.earthdatacloud.nasa.gov"}
PRODUCTS = {
    "VNP14IMG": ("SNPP", "fire", "002"),
    "VNP03IMG": ("SNPP", "geolocation", "002"),
    "VJ114IMG": ("N20", "fire", "002"),
    "VJ103IMG": ("N20", "geolocation", "021"),
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pending")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked_spec(package):
    spec_path = package / "production_manifest.json"
    spec = json.loads(spec_path.read_text())
    require(spec["protocol"] == "gcp_full_training_queue_v1", "Production protocol")
    require(
        set(spec["files"])
        == {
            "summer.zip",
            "compact.py",
            "pairs.csv",
            "sources.csv",
            "july_verification.json",
            "run_gcp_production.py",
            "gcp_production_support.py",
            "verified_job_store.py",
            "drive_job_store.py",
            "production_drive_store.py",
            "requirements.txt",
        },
        "Production package file set",
    )
    require(spec["negative_label_permitted"] is False, "Production label policy")
    require(spec["training_start"] == "2018-01-01", "Training start")
    require(spec["training_end_exclusive"] == "2024-01-01", "Training end")
    require(spec["completed_months"] == ["2023-07"], "Completed month scope")
    for name, checksum in spec["files"].items():
        require(Path(name).name == name and "\\" not in name, "Production package path")
        require(digest(package / name) == checksum, "Production package changed")
    require(spec["files"]["summer.zip"] == SUMMER_SHA, "Frozen pair science changed")
    require(spec["files"]["compact.py"] == COMPACT_SHA, "Frozen daily science changed")
    july = json.loads((package / "july_verification.json").read_text())
    require(july["status"] == "independent_month_compact_readback_passed", "July proof status")
    require(
        july["complete_month"] is True and july["completed_days"] == 31, "July proof completeness"
    )
    require(july["negative_label_permitted"] is False, "July proof labels")
    return spec, digest(spec_path)


def read_scope(package):
    spec, scope_sha = checked_spec(package)
    pairs = pd.read_csv(package / "pairs.csv", dtype={"pair_key": str})
    sources = pd.read_csv(package / "sources.csv", dtype={"pair_key": str})
    require(pairs.day.between("2018-01-01", "2023-12-31").all(), "Sealed dates in queue")
    require(pairs.negative_label_permitted.eq(False).all(), "Catalogue labels")
    require(sources.start_utc.str[:10].between("2018-01-01", "2023-12-31").all(), "Source dates")
    require(sources.negative_label_permitted.eq(False).all(), "Source labels")
    require(not pairs.duplicated(["sensor", "pair_key"]).any(), "Duplicate queue pair")
    require(sources.concept_id.is_unique, "Duplicate queue source")
    require(not sources.duplicated(["sensor", "pair_key", "role"]).any(), "Duplicate queue role")
    months = set(pairs.day.str[:7]) - {"2023-07"}
    require(len(months) == 71 and set(spec["months"]) == months, "Full 71-month queue required")
    require(len(spec["months"]) == len(months), "Repeated queue month")
    require(spec["months"][0] == "2023-08", "First production month")
    nominal = pairs.loc[pairs.pair_status.eq("nominal_unique_pair")]
    require(len(nominal) == 18711, "Frozen nominal pair population")
    require(
        set(nominal.day) == set(pd.date_range("2018-01-01", "2023-12-31").strftime("%Y-%m-%d")),
        "Every training day needs nominal sources",
    )
    require(
        len(nominal.loc[~nominal.day.str.startswith("2023-07")])
        == spec["full_remaining_nominal_pairs"]
        == 18441,
        "Full remaining pair scope",
    )
    joined = sources.merge(nominal[["sensor", "pair_key", "day"]], validate="many_to_one")
    require(len(joined) == 2 * len(nominal), "Nominal source population")
    roles = joined.groupby(["sensor", "pair_key"]).role.agg(list)
    require(all(sorted(r) == ["fire", "geolocation"] for r in roles), "Nominal roles")
    require(joined.start_utc.str[:10].eq(joined.day).all(), "Nominal date identity")
    return spec, scope_sha, pairs, joined


def source_size(row, metadata):
    # Series.product is a method; normalize records before accessing this column.
    if isinstance(row, pd.Series):
        row = SimpleNamespace(**row.to_dict())
    require(
        re.fullmatch(
            r"(VNP14IMG|VNP03IMG|VJ114IMG|VJ103IMG)\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc", row.filename
        ),
        "NASA filename",
    )
    expected = PRODUCTS.get(row.product)
    require(expected == (row.sensor, row.role, row.filename.split(".")[3]), "Product identity")
    require(
        ".".join(row.filename.split(".")[1:3]).removeprefix("A") == row.pair_key,
        "Filename pair key",
    )
    url = urlsplit(row.data_url)
    require(
        url.scheme == "https"
        and url.hostname in DATA_HOSTS
        and not url.username
        and not url.password
        and url.path.rsplit("/", 1)[-1] == row.filename,
        "NASA download URL",
    )
    require(
        {
            r["Identifier"].removesuffix(".nc")
            for r in metadata["DataGranule"]["Identifiers"]
            if r["IdentifierType"] == "ProducerGranuleId"
        }
        == {row.filename.removesuffix(".nc")},
        "UMM producer identity",
    )
    collection = metadata["CollectionReference"]
    require(collection["ShortName"] == row.product, "UMM product")
    require(
        collection["Version"] in ({"2.1", "021"} if row.product == "VJ103IMG" else {"2", "002"}),
        "UMM version",
    )
    dates = metadata["TemporalExtent"]["RangeDateTime"]
    require(
        pd.Timestamp(dates["BeginningDateTime"]) == pd.Timestamp(row.start_utc)
        and pd.Timestamp(dates["EndingDateTime"]) == pd.Timestamp(row.end_utc),
        "UMM interval",
    )
    require(row.data_url in {r["URL"] for r in metadata["RelatedUrls"]}, "UMM data URL")
    entries = metadata["DataGranule"]["ArchiveAndDistributionInformation"]
    require(len(entries) == 1, "UMM ambiguous archive")
    entry = entries[0]
    size = entry.get("SizeInBytes")
    if size is None:
        require(entry["SizeUnit"] == "MB", "UMM size unit")
        size = round(entry["Size"] * 2**20)
    require(type(size) is int and 0 < size < 1_000_000_000, "UMM exact source size")
    require(abs(size - row.catalogue_size_bytes_estimate) <= 1, "UMM catalogue size")
    return size


def public_metadata(concept, cache):
    require(re.fullmatch(r"G\d+-[A-Z0-9]+", concept), "Metadata concept identity")
    path = cache / f"{concept}.json"
    if not path.exists():
        for attempt in range(3):
            try:
                url = f"https://cmr.earthdata.nasa.gov/search/concepts/{concept}.umm_json"
                with urllib.request.urlopen(url, timeout=45) as response:
                    require(
                        urlsplit(response.geturl()).hostname == "cmr.earthdata.nasa.gov", "CMR host"
                    )
                    data = response.read(2_000_001)
                require(len(data) <= 2_000_000, "UMM size bound")
                atomic_json(path, json.loads(data))
                break
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == 2:
                    raise RuntimeError("Public metadata transport failed") from None
                time.sleep(2**attempt)
    return json.loads(path.read_text())


def month_names(rows):
    return {"month.json", *[str(c) + ".json" for c in rows.concept_id]}


def build_month(month, rows, catalog, cache, destination, fetch=public_metadata):
    require(rows.day.str.startswith(month).all(), "Mixed metadata month")
    require(len(rows) > 0 and rows.concept_id.is_unique, "Month metadata scope")
    destination.mkdir(parents=True, exist_ok=True)
    pairs = []
    for (sensor, key), group in rows.groupby(["sensor", "pair_key"], sort=True):
        require(
            len(group) == 2 and set(group.role) == {"fire", "geolocation"}, "Metadata pair roles"
        )
        starts, ends = set(group.start_utc), set(group.end_utc)
        require(len(starts) == len(ends) == 1, "Pair interval mismatch")
        pair = {
            "sensor": sensor,
            "key": key,
            "sample_id": f"{sensor}:{key}",
            "stem": "l2_sample_" + ("N20_" if sensor == "N20" else "") + key,
            "start_utc": next(iter(starts)),
            "end_utc": next(iter(ends)),
            "sources": [],
            "metadata": {},
        }
        for row in group.itertuples():
            metadata = fetch(row.concept_id, cache)
            size = source_size(row, metadata)
            name = row.concept_id + ".json"
            (destination / name).write_bytes(json_bytes(metadata))
            pair["metadata"][row.role] = "production_metadata/" + name
            pair["sources"].append(
                {
                    "role": row.role,
                    "filename": row.filename,
                    "url": row.data_url,
                    "bytes": size,
                    "provider": "LPCLOUD" if row.role == "fire" else "LAADS",
                    "metadata_sha256": digest(destination / name),
                }
            )
        pairs.append(pair)
    days = (
        pd.date_range(month + "-01", periods=pd.Period(month).days_in_month)
        .strftime("%Y-%m-%d")
        .tolist()
    )
    missing = catalog.loc[
        catalog.day.str.startswith(month) & ~catalog.pair_status.eq("nominal_unique_pair")
    ]
    manifest = {
        "month": month,
        "days": days,
        "pairs": pairs,
        "unpaired_catalogue_records": missing.fillna("").to_dict("records"),
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }
    atomic_json(destination / "month.json", manifest)
    return manifest


def validate_month(path, month, rows, catalog, destination=None):
    with zipfile.ZipFile(path) as archive:
        require(set(archive.namelist()) == month_names(rows), "Month manifest ZIP members")
        require(
            len(archive.namelist()) == len(set(archive.namelist())), "Month manifest duplicates"
        )
        require(archive.testzip() is None, "Month manifest CRC")
        manifest = json.loads(archive.read("month.json"))
        require(
            manifest["month"] == month and manifest["negative_label_permitted"] is False,
            "Month identity/policy",
        )
        require(manifest["daily_observation_status"] == "unknown", "Month observation policy")
        days = (
            pd.date_range(month + "-01", periods=pd.Period(month).days_in_month)
            .strftime("%Y-%m-%d")
            .tolist()
        )
        require(manifest["days"] == days, "Month calendar changed")
        ids = {f"{r.sensor}:{r.pair_key}" for r in rows.itertuples()}
        require(len(manifest["pairs"]) == len(ids), "Month manifest pair count")
        require({p["sample_id"] for p in manifest["pairs"]} == ids, "Month manifest pair set")
        actual_missing = (
            catalog.loc[
                catalog.day.str.startswith(month) & ~catalog.pair_status.eq("nominal_unique_pair")
            ]
            .fillna("")
            .to_dict("records")
        )
        require(manifest["unpaired_catalogue_records"] == actual_missing, "Unpaired records lost")
        for pair in manifest["pairs"]:
            require(pair["sample_id"] == f"{pair['sensor']}:{pair['key']}", "Saved pair identity")
            group = rows.loc[rows.sensor.eq(pair["sensor"]) & rows.pair_key.eq(pair["key"])]
            require(len(pair["sources"]) == 2, "Manifest source count")
            require(
                {s["role"] for s in pair["sources"]} == {"fire", "geolocation"},
                "Manifest source roles",
            )
            for source in pair["sources"]:
                row = group.loc[group.role.eq(source["role"])].iloc[0]
                data = archive.read(row.concept_id + ".json")
                require(
                    hashlib.sha256(data).hexdigest() == source["metadata_sha256"], "Saved UMM SHA"
                )
                require(source_size(row, json.loads(data)) == source["bytes"], "Saved UMM bytes")
                require(
                    source["filename"] == row.filename and source["url"] == row.data_url,
                    "Saved source identity",
                )
                require(
                    source["provider"] == ("LPCLOUD" if row.role == "fire" else "LAADS"),
                    "Saved provider",
                )
                require(
                    pair["metadata"][source["role"]]
                    == "production_metadata/" + row.concept_id + ".json",
                    "Saved metadata path",
                )
            require(
                pair["start_utc"] == group.iloc[0].start_utc
                and pair["end_utc"] == group.iloc[0].end_utc,
                "Saved pair time",
            )
            expected_stem = "l2_sample_" + ("N20_" if pair["sensor"] == "N20" else "") + pair["key"]
            require(pair["stem"] == expected_stem, "Saved pair stem")
        if destination is not None:
            destination.mkdir(parents=True, exist_ok=True)
            for name in archive.namelist():
                (destination / name).write_bytes(archive.read(name))
    return manifest


def pack_flat(folder, names, path):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            require(Path(name).name == name, "Flat product name")
            archive.write(folder / name, name)


def template(package, root):
    require(digest(package / "summer.zip") == SUMMER_SHA, "Frozen template identity")
    require(not root.is_symlink(), "Template root symlink")
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package / "summer.zip") as archive:
        manifest = json.loads(archive.read("summer/manifest.json"))
        names = set(manifest["bundle_files"]) | {"summer/manifest.json"}
        require(
            set(archive.namelist()) == names and len(archive.namelist()) == len(names),
            "Template members",
        )
        require(archive.testzip() is None, "Template CRC")
        for name in names:
            target = (root / name).resolve()
            require(target.is_relative_to(root.resolve()), "Template path")
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(name)
            if target.exists():
                require(target.read_bytes() == data, "Existing frozen template changed")
            else:
                target.write_bytes(data)
            if name in manifest["bundle_files"]:
                require(digest(target) == manifest["bundle_files"][name], "Frozen science file")
    require(digest(package / "compact.py") == COMPACT_SHA, "Compact code identity")
    target = root / "scripts/cloud/l2_daily_compact.py"
    if target.exists():
        require(digest(target) == COMPACT_SHA, "Existing compact changed")
    else:
        shutil.copyfile(package / "compact.py", target)


def science(root):
    # Validate the clone before importing code or trusting geography/provenance.
    manifest_path = root / "summer/manifest.json"
    require(digest(manifest_path) == SUMMER_MANIFEST_SHA, "Frozen science manifest changed")
    manifest = json.loads(manifest_path.read_text())
    for name, checksum in manifest["bundle_files"].items():
        target = root / name
        require(target.resolve().is_relative_to(root.resolve()), "Science clone path")
        require(digest(target) == checksum, "Frozen science clone changed")
    require(
        digest(root / "scripts/cloud/l2_daily_compact.py") == COMPACT_SHA,
        "Daily science clone changed",
    )
    compact = load("production_daily_science", root / "scripts/cloud/l2_daily_compact.py")
    return compact, compact.summer


def owned_remove(target, base):
    target, base = Path(target), Path(base).resolve()
    require(
        not target.is_symlink() and target.resolve().is_relative_to(base), "Scratch cleanup escape"
    )
    require(target.resolve() != base, "Never remove scratch root")
    if target.exists():
        shutil.rmtree(target)
