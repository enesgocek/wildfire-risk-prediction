"""Read selected training scan rows once per monthly payload, entirely offline."""

import hashlib
import io
import json
import socket
import time
import zipfile
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.observation_window import FIELDS, KEYS

PARTS_SHA = "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9"
COMPACT_SHA = "f09e73837732160a65cc059c382c2ed85a95de0985aa470c1ec5789f6dc17b54"
DELIVERY = "outputs/gcp_delivery/2026-10-14/compact/products"
JULY = "outputs/cloud_month/received/l2_month_2023_07_results.zip"


def deny(*args, **kwargs):
    raise RuntimeError("Offline scan-window source reader")


def read_month(root, report, day_grids, deadline):
    """Hash accepted bytes before reading; return only requested grid/day scan rows."""
    # These checks precede every filesystem operation, including for invalid holdout jobs.
    require(bool(day_grids), "Nonempty source request")
    for day, grids in day_grids.items():
        training_day(day)
        require(day[:7] == report["month"] and bool(grids), "Requested month/grid scope")
        require(
            day in report["days"] and day not in report["missing_source_days"],
            "Only available accepted source days",
        )
    require(
        report["status"] == "observation_month_materialization_passed"
        and report["negative_label_permitted"] is False
        and report["daily_observation_status"] == "unknown",
        "Accepted monthly source",
    )
    root = Path(root)
    inputs, inner, selected = {}, {}, {}

    def payload(name):
        require(time.monotonic() < deadline, "Window source runtime reserve")
        path = root / name
        require(path.is_file() and not path.is_symlink(), "Regular accepted payload")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(digest == report["input_payload_sha256"][name], "Accepted payload hash")
        inputs[name] = digest
        return data

    month_name = DELIVERY + "/month/" + report["month"] + "/payload.zip"
    archive = None
    if report["month"] == "2023-07":
        archive = zipfile.ZipFile(io.BytesIO(payload(JULY)))
    elif month_name in report["input_payload_sha256"]:
        archive = zipfile.ZipFile(io.BytesIO(payload(month_name)))
    try:
        for day, grids in sorted(day_grids.items()):
            require(time.monotonic() < deadline, "Window source runtime reserve")
            if report["month"] == "2023-07":
                raw = {n: archive.read(day + "/" + n) for n in ("report.json", "scan_grid.csv")}
            else:
                data = (
                    archive.read(day + ".zip")
                    if archive
                    else payload(DELIVERY + "/day/" + day + "/payload.zip")
                )
                with zipfile.ZipFile(io.BytesIO(data)) as daily:
                    raw = {n: daily.read(n) for n in ("report.json", "scan_grid.csv")}
            daily = json.loads(raw["report.json"])
            hashes = {n: hashlib.sha256(b).hexdigest() for n, b in raw.items()}
            require(
                daily["day"] == day
                and daily["parts_sha256"] == PARTS_SHA
                and daily["compact_code_sha256"] == COMPACT_SHA
                and daily["daily_observation_status"] == "unknown"
                and daily["negative_label_permitted"] is False
                and daily["outputs_sha256"]["scan_grid.csv"] == hashes["scan_grid.csv"],
                "Accepted daily scan identity",
            )
            frame = pd.read_csv(
                io.BytesIO(raw["scan_grid.csv"]), usecols=FIELDS, dtype={"pair_key": str}
            )
            require(not frame.duplicated(KEYS).any(), "Unique daily scan-grid keys")
            frame = frame.loc[frame.grid_id.isin(grids)].copy()
            frame["source_nominal_day"] = day
            selected[day] = frame
            inner[day] = hashes
    finally:
        if archive:
            archive.close()
    return {"month": report["month"], "inputs": inputs, "inner": inner, "frames": selected}


def read_month_offline(*args):
    """Install the network guard in each independent local process."""
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    return read_month(*args)
