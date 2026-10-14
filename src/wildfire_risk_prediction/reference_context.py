"""Official narrative context cannot certify event identity, ignition time or binary labels."""

import json
from html.parser import HTMLParser

import pandas as pd

from wildfire_risk_prediction.feature_join import require


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def verify_page(data, source):
    require(data and len(data) <= 3_000_000, "Bounded public reference page")
    parser = VisibleText()
    parser.feed(data.decode("utf-8-sig", errors="strict"))
    text = " ".join(" ".join(parser.parts).split())
    require(
        all(term in text for term in source["required_visible_terms"]),
        "Reference visible content differs from inspected claims",
    )
    # Term matching only guards retrieval/content drift; claims were inspected separately.
    return text


def link_context(cases, catalog):
    require(
        catalog["scope"] == "training_case_context_only" and catalog["labels_permitted"] is False,
        "Context cannot open label gates",
    )
    require(
        cases.cluster_id.is_unique and cases.event_status.eq("exploratory_cluster_only").all(),
        "Unique exploratory review cases",
    )
    dates = pd.to_datetime(cases.first_detection_utc, utc=True, errors="raise")
    require(dates.dt.year.between(2018, 2023).all(), "Training cases only")
    rows = []
    for source in catalog["sources"]:
        selection = source["candidate_case_selection"]
        if selection is None:
            continue
        ids = selection["case_ids"]
        require(
            ids and len(ids) == len(set(ids)) and set(ids) <= set(cases.cluster_id),
            "Exact candidate case identities exist",
        )
        selected = cases.set_index("cluster_id").loc[ids]
        require(
            pd.to_datetime(selected.first_detection_utc, utc=True)
            .dt.strftime("%Y-%m-%d")
            .eq(selection["first_detection_utc_date"])
            .all(),
            "Context date selection agrees",
        )
        for case in selected.itertuples():
            rows.append(
                {
                    "review_unit_id": f"event:{case.scenario}:{case.Index}",
                    "cluster_id": case.Index,
                    "scenario": case.scenario,
                    "membership_sha256": case.membership_sha256,
                    "first_detection_utc": case.first_detection_utc,
                    "last_detection_utc": case.last_detection_utc,
                    "detection_count": case.detection_count,
                    "earliest_grid_ids_json": case.earliest_grid_ids_json,
                    "first_grid_count": len(json.loads(case.earliest_grid_ids_json)),
                    "source_id": source["source_id"],
                    "source_url": source["url"],
                    "correspondence_status": "candidate_regional_context_only",
                    "multiple_reported_origins_review": True,
                    "exact_event_identity_proven": False,
                    "first_cell_identity_proven": False,
                    "ignition_timestamp_utc": pd.NA,
                    "target": pd.NA,
                }
            )
    require(rows, "Context candidates present")
    return pd.DataFrame(rows)
