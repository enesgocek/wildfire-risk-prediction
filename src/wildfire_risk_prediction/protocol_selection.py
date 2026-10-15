"""Describe selection within a purpose-chosen pilot, without choosing a label policy."""

import itertools

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require, training_day

SCREENS = {
    "daily_land": "nominal_land_fraction",
    "repeat_12h": "repeat_12h_fraction",
    "all_four_bins": "nominal_land_all_four_bins_fraction",
}
CUTS = (0.5, 0.8, 0.9, 0.95, 0.99)
GROUPS = ("primary_province", "calendar_season", "cover_group", "signal_group", "year")


def describe_selection(units, cuts=CUTS):
    """Return per-unit screens, marginal strata and paired disagreements on identical units."""
    frame = units.copy(deep=True).reset_index(drop=True)
    require(len(frame) > 0 and frame.review_unit_id.is_unique, "Nonempty unique pilot units")
    require(
        frame[["review_unit_id", "grid_id", "target_day"]].notna().all().all()
        and not frame.duplicated(["grid_id", "target_day"]).any(),
        "Unique complete grid/day identities",
    )
    dates = frame.target_day.map(training_day)
    frame["year"] = dates.map(lambda d: str(d.year))
    seasons = {
        12: "winter",
        1: "winter",
        2: "winter",
        3: "spring",
        4: "spring",
        5: "spring",
        6: "summer",
        7: "summer",
        8: "summer",
        9: "autumn",
        10: "autumn",
        11: "autumn",
    }
    require(frame.calendar_season.eq(dates.map(lambda d: seasons[d.month])).all(), "Season dates")
    for name in GROUPS:
        require(
            frame[name].map(lambda x: isinstance(x, str) and bool(x.strip())).all(),
            "Complete descriptive strata",
        )
    require(frame.target.isna().all(), "No admitted targets in method pilot")
    require(frame.daily_observation_status.eq("unknown").all(), "Unknown observation status")
    for name in ("negative_label_permitted", "labels_created", "accepted_label_rule"):
        boolean(frame[name], name)
        require(not frame[name].any(), "Closed label acceptance")
    thermal = frame.thermal_center_definite_count.to_numpy(float)
    require(
        np.isfinite(thermal).all()
        and (thermal >= 0).all()
        and (thermal == np.floor(thermal)).all(),
        "Integer thermal witness counts",
    )
    require(
        frame.signal_group.eq(
            np.where(thermal > 0, "thermal_center_present", "no_selected_thermal_center")
        ).all(),
        "Selection group agrees with actual target-window thermal witnesses",
    )
    values = frame[list(SCREENS.values())].to_numpy(float)
    require(
        np.isfinite(values).all() and (values >= 0).all() and (values <= 1 + 1e-8).all(),
        "Finite nominal support fractions within numerical tolerance",
    )
    require((values[:, 1:] <= values[:, :1] + 1e-8).all(), "Repeated support within daily support")
    require(
        cuts and len(set(cuts)) == len(cuts) and all(np.isfinite(c) and 0 < c <= 1 for c in cuts),
        "Distinct explanatory area cuts",
    )
    strata = [("all", "all", frame.index)]
    for name in GROUPS:
        strata.extend((name, str(value), group.index) for value, group in frame.groupby(name))
    strata.extend(
        ("province_signal", f"{province}|{signal}", group.index)
        for (province, signal), group in frame.groupby(["primary_province", "signal_group"])
    )
    rows, summaries, paired = [], [], []
    for cut in cuts:
        passed = pd.DataFrame({k: frame[v].ge(cut) for k, v in SCREENS.items()})
        for index, unit in frame.iterrows():
            rows.append(
                {
                    "review_unit_id": unit.review_unit_id,
                    "grid_id": unit.grid_id,
                    "target_day": unit.target_day,
                    "area_fraction_cut": cut,
                    **{f"{k}_screen": bool(passed.loc[index, k]) for k in SCREENS},
                    "accepted_label_rule": False,
                    "negative_label_permitted": False,
                    "daily_observation_status": "unknown",
                    "target": None,
                }
            )
        for dimension, value, ids in strata:
            selected = frame.loc[ids]
            common = {
                "dimension": dimension,
                "stratum": value,
                "area_fraction_cut": cut,
                "denominator_units": len(ids),
                "denominator_grids": selected.grid_id.nunique(),
                "denominator_dates": selected.target_day.nunique(),
                "purpose_selected_sample": True,
                "accepted_label_rule": False,
            }
            for screen in SCREENS:
                subset = selected.loc[passed.loc[ids, screen]]
                summaries.append(
                    {
                        **common,
                        "screen": screen,
                        "passing_units": len(subset),
                        "excluded_units": len(ids) - len(subset),
                        "passing_fraction_of_stratum": len(subset) / len(ids),
                        "passing_grids": subset.grid_id.nunique(),
                        "passing_dates": subset.target_day.nunique(),
                    }
                )
            for left, right in itertools.combinations(SCREENS, 2):
                a, b = passed.loc[ids, left], passed.loc[ids, right]
                counts = {
                    "both_pass": int((a & b).sum()),
                    "left_only": int((a & ~b).sum()),
                    "right_only": int((~a & b).sum()),
                    "neither_pass": int((~a & ~b).sum()),
                }
                require(sum(counts.values()) == len(ids), "Paired cohort conservation")
                paired.append({**common, "left_screen": left, "right_screen": right, **counts})
    return pd.DataFrame(rows), pd.DataFrame(summaries), pd.DataFrame(paired)
