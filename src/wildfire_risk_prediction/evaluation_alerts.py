"""Daily cell alert arithmetic, retaining unadjudicated alarms separately from false alarms."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require, utc_times


def daily_alerts(frame, *, capacity, tie_policy):
    """Technical tie option must be explicit; no operational K or event hit policy chosen."""
    require(type(capacity) is int and capacity > 0, "Explicit positive daily capacity")
    require(tie_policy == "grid_id_ascending", "Explicit supported tie policy")
    required = {"grid_id", "prediction_timestamp_utc", "probability", "target"}
    require(required <= set(frame.columns) and len(frame) > 0, "Complete alert input")
    work = frame.copy().reset_index(drop=True)
    require(
        work.grid_id.map(lambda x: isinstance(x, str) and bool(x.strip())).all()
        and not work.duplicated(["grid_id", "prediction_timestamp_utc"]).any(),
        "Unique alert grid/day identities",
    )
    times = utc_times(work.prediction_timestamp_utc)
    require(
        times.notna().all()
        and times.eq(times.dt.normalize()).all()
        and times.dt.year.between(2018, 2023).all(),
        "Training-only daily UTC alert rehearsal",
    )
    require(
        pd.MultiIndex.from_arrays([work.grid_id, times]).is_unique,
        "Canonical UTC alert identities must be unique",
    )
    p = work.probability.to_numpy()
    require(
        p.dtype.kind in "biuf" and np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(),
        "Finite alert probabilities in [0,1]",
    )
    known = work.target.dropna()
    require(
        known.map(
            lambda x: (
                isinstance(x, (int, float, np.number))
                and not isinstance(x, (bool, np.bool_))
                and x in (0, 1)
            )
        ).all(),
        "Binary or unadjudicated targets only",
    )
    work["selected"] = False
    summaries = []
    # Group on parsed timestamps so Z/+00:00 spelling cannot double the same daily capacity.
    for day, indices in work.groupby(times).groups.items():
        group = work.loc[indices].sort_values(
            ["probability", "grid_id"], ascending=[False, True], kind="stable"
        )
        selected = group.head(capacity)
        work.loc[selected.index, "selected"] = True
        adjudicated = int(group.target.notna().sum())
        false_count = int(selected.target.eq(0).sum())
        summaries.append(
            {
                "prediction_timestamp_utc": day.isoformat(),
                "candidate_units": len(group),
                "adjudicated_units": adjudicated,
                "unknown_units": int(group.target.isna().sum()),
                "selected_cells": len(selected),
                "selected_positive_cells": int(selected.target.eq(1).sum()),
                "selected_verified_negative_cells": false_count,
                "selected_unadjudicated_cells": int(selected.target.isna().sum()),
                "verified_false_alerts_per_1000_adjudicated_units": (
                    1000 * false_count / adjudicated if adjudicated else None
                ),
                "unique_event_recall": None,
                "event_hit_policy_accepted": False,
            }
        )
    return work, pd.DataFrame(summaries)
