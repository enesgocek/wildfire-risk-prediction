"""Require complete native scan witnesses before omitting out-of-window raw geometry."""

import numpy as np

from wildfire_risk_prediction.feature_join import require


def required_pairs(pairs, witnesses):
    ids = [p["sample_id"] for p in pairs]
    require(
        len(ids) == len(set(ids))
        and witnesses.sample_id.is_unique
        and set(witnesses.sample_id) == set(ids),
        "Exact complete witness inventory",
    )
    table = witnesses.set_index("sample_id").loc[ids]
    counts = table[
        ["scan_count", "inside_scan_count", "boundary_scan_count", "outside_scan_count"]
    ].to_numpy(float)
    require(
        np.isfinite(counts).all()
        and (counts >= 0).all()
        and (counts == np.floor(counts)).all()
        and (counts[:, 0] > 0).all(),
        "Positive complete native scan counts",
    )
    require(
        np.array_equal(counts[:, 0], counts[:, 1:].sum(axis=1)), "All scan decisions reconciled"
    )
    keep = counts[:, 1] + counts[:, 2] > 0
    expected = np.where(keep, "retain_raw_inside_or_boundary", "outside_by_full_scan_witness")
    require(np.array_equal(table.decision, expected), "Witness decision matches all native scans")
    for pair, (_, row) in zip(pairs, table.iterrows(), strict=True):
        require(
            pair["bytes"] == row.raw_bytes and pair["source_day"] == row.source_nominal_day,
            "Same source day and raw inventory",
        )
    return [p for p, retain in zip(pairs, keep, strict=True) if retain]
