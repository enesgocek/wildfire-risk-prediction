"""Linux-only bounded resource sampling; never read cmdline, environ or credentials."""

import csv
import os
import shutil
import threading
import time
from pathlib import Path


def cpu_times(text):
    row = next(line.split() for line in text.splitlines() if line.startswith("cpu "))
    values = [int(v) for v in row[1:9]]
    return sum(values), values[3], values[4], values[7]


def memory_values(text):
    rows = {line.split(":")[0]: int(line.split()[1]) * 1024 for line in text.splitlines()}
    return rows["MemTotal"], rows["MemAvailable"]


def net_bytes(text):
    rx = tx = 0
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, numbers = line.split(":", 1)
        if name.strip() == "lo":
            continue
        values = numbers.split()
        rx += int(values[0])
        tx += int(values[8])
    return rx, tx


def descendant_rss(parent):
    rows = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            data = path.read_text()
            pid = int(path.parent.name)
            fields = data[data.rindex(")") + 2 :].split()
            rows[pid] = (int(fields[1]), max(0, int(fields[21])) * os.sysconf("SC_PAGE_SIZE"))
        except (OSError, ValueError, IndexError):
            continue  # Short-lived processes can disappear while sampled.
    owned = {parent}
    while True:
        added = {pid for pid, (ppid, _) in rows.items() if ppid in owned} - owned
        if not added:
            break
        owned |= added
    return sum(rows[pid][1] for pid in owned if pid in rows), len(owned) - 1


class Sampler:
    FIELDS = (
        "seconds",
        "arm",
        "phase",
        "cpu_busy_pct",
        "cpu_iowait_pct",
        "cpu_steal_pct",
        "vm_mem_used_bytes",
        "mem_available_bytes",
        "process_tree_rss_bytes",
        "descendants",
        "disk_free_bytes",
        "network_rx_bytes",
        "network_tx_bytes",
    )

    def __init__(self, root):
        self.root, self.rows = root, []
        self.arm, self.phase = "setup", "setup"
        self.stop_event = threading.Event()
        self.failed = False
        self.start = time.monotonic()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def collect(self, previous):
        cpu = cpu_times(Path("/proc/stat").read_text())
        total, available = memory_values(Path("/proc/meminfo").read_text())
        rx, tx = net_bytes(Path("/proc/net/dev").read_text())
        rss, descendants = descendant_rss(os.getpid())
        free = shutil.disk_usage(self.root).free
        elapsed = cpu[0] - previous[0] if previous else 0
        idle = cpu[1] - previous[1] if previous else 0
        wait = cpu[2] - previous[2] if previous else 0
        steal = cpu[3] - previous[3] if previous else 0

        def pct(value):
            return round(100 * value / elapsed, 3) if elapsed > 0 else None

        self.rows.append(
            {
                "seconds": round(time.monotonic() - self.start, 3),
                "arm": self.arm,
                "phase": self.phase,
                "cpu_busy_pct": pct(elapsed - idle - wait - steal),
                "cpu_iowait_pct": pct(wait),
                "cpu_steal_pct": pct(steal),
                "vm_mem_used_bytes": total - available,
                "mem_available_bytes": available,
                "process_tree_rss_bytes": rss,
                "descendants": descendants,
                "disk_free_bytes": free,
                "network_rx_bytes": rx,
                "network_tx_bytes": tx,
            }
        )
        # Failure aborts the test; it never changes another job or resource configuration.
        if available < 4 * 2**30 or free < 4 * 2**30:
            self.failed = True
        return cpu

    def loop(self):
        previous = None
        while not self.stop_event.is_set():
            try:
                previous = self.collect(previous)
            except Exception:
                self.failed = True  # Missing telemetry must not become a false zero.
            self.stop_event.wait(2)

    def begin(self):
        self.thread.start()

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=10)
        path = self.root / "resource_samples.csv"
        with path.open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)

    def summary(self, arm):
        rows = [r for r in self.rows if r["arm"] == arm and r["cpu_busy_pct"] is not None]
        if not rows:
            return {"valid": False}
        return {
            "valid": True,
            "samples": len(rows),
            "mean_cpu_busy_pct": sum(r["cpu_busy_pct"] for r in rows) / len(rows),
            "peak_cpu_busy_pct": max(r["cpu_busy_pct"] for r in rows),
            "peak_vm_mem_used_bytes": max(r["vm_mem_used_bytes"] for r in rows),
            "peak_sampled_process_tree_rss_bytes": max(r["process_tree_rss_bytes"] for r in rows),
            "min_mem_available_bytes": min(r["mem_available_bytes"] for r in rows),
            "min_disk_free_bytes": min(r["disk_free_bytes"] for r in rows),
            "network_rx_bytes": rows[-1]["network_rx_bytes"] - rows[0]["network_rx_bytes"],
            "network_tx_bytes": rows[-1]["network_tx_bytes"] - rows[0]["network_tx_bytes"],
        }
