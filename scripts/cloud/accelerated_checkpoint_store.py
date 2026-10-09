"""Single-writer indexed Drive metadata; payload bytes always freshly read from Drive.

Same immutable checkpoint schema as the frozen worker. The controller has its
own manifest; it does not change the identity of scientific child code.
"""

import json
import threading

from drive_job_store import MARKER_MIMES, MAX_BYTES, PAYLOAD_MIMES, DriveJobStore, require
from verified_job_store import VerifiedJobStore, canonical, sha

FIELDS = "id,name,size,mimeType,appProperties"


class IndexedDriveStore(DriveJobStore):
    def __init__(self, api, folder_id):
        super().__init__(api, folder_id)
        self.index = {}
        self.lock = threading.RLock()

    def query(self, job, name=None):
        result = (
            f"'{self.folder_id}' in parents and trashed = false "
            f"and appProperties has {{ key='job' and value='{job}' }}"
        )
        return result + (f" and name = '{name}'" if name else "")

    def populate(self, job):
        if job not in self.index:
            rows = self.validate_entries(self.api.listing(self.query(job)))
            require(all(r["appProperties"]["job"] == job for r in rows), "Indexed scope identity")
            self.index[job] = {r["name"]: r for r in rows}
        return self.index[job]

    def get(self, key):
        with self.lock:
            name, job = self.name(key), self.job(key)
            row = self.populate(job).get(name)
            if row is None:
                return None  # Single writer; every new create does a fresh collision lookup.
            live = self.metadata(row["id"])
            require(live == row, "Indexed metadata changed")
            require(
                live["mimeType"] in (PAYLOAD_MIMES if key.endswith(".zip") else MARKER_MIMES),
                "Indexed MIME role",
            )
            data = self.api.request(f"/files/{live['id']}?alt=media")
            require(len(data) == int(live["size"]) <= MAX_BYTES, "Indexed byte size")
            return data

    def metadata(self, identity):
        value = json.loads(self.api.request(f"/files/{identity}?fields={FIELDS},parents,trashed"))
        require(
            value.get("trashed") is False and value.get("parents") == [self.folder_id],
            "Indexed parent/trash changed",
        )
        row = {name: value[name] for name in FIELDS.split(",")}
        self.validate_entries([row])
        return row

    def create(self, key, data):
        with self.lock:
            require(0 < len(data) <= MAX_BYTES, "Indexed write bound")
            name, job = self.name(key), self.job(key)
            index = self.populate(job)
            live = self.validate_entries(self.api.listing(self.query(job, name)))
            require(len(live) <= 1, "Duplicate live indexed object")
            if live:
                require(
                    live[0]["appProperties"]["job"] == job and live[0]["name"] == name,
                    "Live collision scope",
                )
                index[name] = live[0]
                require(self.get(key) == data, "Immutable indexed collision")
                return
            require(name not in index, "Indexed object disappeared")
            identity = self.api.create_file(
                {
                    "name": name,
                    "parents": [self.folder_id],
                    "mimeType": "application/zip" if key.endswith(".zip") else "application/json",
                    "appProperties": {
                        "protocol": "wildfire_store_v1",
                        "key_hash": name.removesuffix(".object"),
                        "job": job,
                    },
                },
                data,
            )
            row = self.metadata(identity)
            require(
                row["id"] == identity
                and row["name"] == name
                and row["appProperties"]["job"] == job
                and int(row["size"]) == len(data),
                "Created indexed identity",
            )
            index[name] = row

    def used_bytes(self, prefix):
        return sum(int(r["size"]) for r in self.populate(self.job(prefix)).values())


class AcceleratedCheckpointStore(VerifiedJobStore):
    def save(self, task_id, payload, expected_names, scientific_check):
        with self.lock:
            data = payload.read_bytes()
            digest = sha(data)
            existing = self.restore(task_id, expected_names, scientific_check)
            if existing is not None:
                require(existing["payload_sha256"] == digest, "Completed task replacement refused")
                return existing
            self.check_zip(payload, expected_names)
            scientific_check(payload)  # Full local science, before upload.
            prefix = self.task_prefix(task_id)
            key = f"{prefix}/{digest}.zip"
            record = {
                "protocol": "verified_job_checkpoint_v1",
                "task_id": task_id,
                "manifest_sha256": self.manifest_sha,
                "worker_sha256": self.worker_sha,
                "payload_sha256": digest,
                "payload_bytes": len(data),
                "payload_key": key,
                "negative_label_permitted": False,
                "daily_observation_status": "unknown",
            }
            previous = self.backend.get(key)
            require(previous is None or previous == data, "Orphan payload changed")
            addition = (0 if previous is not None else len(data)) + len(canonical(record))
            require(
                self.backend.used_bytes(f"jobs/{self.manifest_sha}") + addition
                <= self.budget_bytes,
                "Accelerated storage budget",
            )
            self.backend.create(key, data)
            readback = self.backend.get(key)
            require(readback == data, "Fresh upload bytes differ")
            self.materialize_checked(readback, expected_names, scientific_check)
            require(payload.read_bytes() == data, "Local payload changed during publication")
            marker_key = prefix + "/completed.json"
            self.backend.create(marker_key, canonical(record))  # Completion remains last.
            require(self.backend.get(marker_key) == canonical(record), "Fresh completion differs")
            # After completion, prove the current remote payload still matches the exact
            # bytes already subjected to full scientific validation; no byte cache.
            require(self.backend.get(key) == data, "Post-completion payload changed")
            return record


def pair_validator(runner, root, pair, month_sha):
    _, native = runner.science(root)

    def check(path):
        native.restore_pair(path, pair, month_sha, root / "inputs")
        # restore_pair validates the staging checkpoint and compare_pair, including
        # geometry, before copying. A duplicate compare_pair on identical bytes adds
        # no extra invariant. The independent remote readback repeats this full check.
        return json.loads((root / "inputs" / (pair["stem"] + "_checkpoint.json")).read_text())

    return native, check
