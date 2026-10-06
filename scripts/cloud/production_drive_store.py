"""Single-parent production store: indexed lookups, bounded single-writer quota cache."""

from drive_job_store import MARKER_MIMES, MAX_BYTES, PAYLOAD_MIMES, DriveJobStore, require


class ProductionDriveStore(DriveJobStore):
    def __init__(self, api, folder_id):
        super().__init__(api, folder_id)
        self.quota_job = None
        self.quota_bytes = None

    def query(self, job, name=None):
        value = (
            f"'{self.folder_id}' in parents and trashed = false "
            f"and appProperties has {{ key='job' and value='{job}' }}"
        )
        return value + (f" and name = '{name}'" if name else "")

    def get(self, key):
        name, job = self.name(key), self.job(key)
        rows = self.validate_entries(self.api.listing(self.query(job, name)))
        require(len(rows) <= 1, "Duplicate production object")
        if not rows:
            return None
        row = rows[0]
        require(row["name"] == name and row["appProperties"]["job"] == job, "Indexed identity")
        allowed = PAYLOAD_MIMES if key.endswith(".zip") else MARKER_MIMES
        require(row["mimeType"] in allowed, "Indexed object role")
        data = self.api.request(f"/files/{row['id']}?alt=media")
        require(len(data) == int(row["size"]) <= MAX_BYTES, "Indexed download size")
        return data

    def used_bytes(self, prefix):
        job = self.job(prefix)
        if self.quota_job != job:
            rows = self.validate_entries(self.api.listing(self.query(job)))
            require(all(r["appProperties"]["job"] == job for r in rows), "Quota job identity")
            self.quota_bytes = sum(int(r["size"]) for r in rows)
            self.quota_job = job
        return self.quota_bytes

    def create(self, key, data):
        # One parent and one VM lock only. Any API failure aborts the invocation;
        # a fresh invocation rebuilds the quota including uncertain/orphan uploads.
        existed = self.get(key) is not None
        self.used_bytes("jobs/" + self.job(key))
        super().create(key, data)
        if not existed:
            self.quota_bytes += len(data)
