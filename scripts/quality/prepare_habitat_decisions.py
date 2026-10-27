"""Assemble an offline decision queue; preserve note provenance and closed gates."""

import csv
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "evidence": (
        "habitat_evidence_review_v1/20261023T155415Z_9d1f8433",
        "abbd061abb08013da6fdf9583c175c4072b041c76abb22819e2d0bdda5b5ca3f",
    ),
    "human1": (
        "preevent_researcher_review_v1/20261023T153234Z_ecee9147",
        "36fac85b3d6fe2f288af7070b70cfed5b037f70bd5b0601646a2eeb38e184645",
    ),
    "human2": (
        "habitat_researcher_notes_v1/20261023T160518Z_3166f1d9",
        "d3e71111b30cc6686eee9319165d9b86b25f9d6c1f2811c4dcbca3ab3e1495fb",
    ),
    "assistant": (
        "remaining_cover_assistant_notes_v1/20261023T162753Z_e27e3f04",
        "7cdaf55d02672447304c7ac2182368f2ff4fa744558edfe899be3a70cf6bae9c",
    ),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins, reports = {}, {}

    def pin(path, expected):
        if sha(path) != expected:
            raise ValueError("Source identity mismatch")
        pins[path.relative_to(ROOT).as_posix()] = expected

    for name, (relative, expected) in SOURCES.items():
        folder = BASE / relative
        pin(folder / "readback.json", expected)
        report = json.loads((folder / "readback.json").read_text(encoding="utf-8"))
        for filename, digest in report.get("artifact_sha256", {}).items():
            pin(folder / filename, digest)
        for key in ("input_sha256", "source_sha256"):
            for filename, digest in report.get(key, {}).items():
                pin(ROOT / filename, digest)
        reports[name] = report
    pin(Path(__file__), sha(Path(__file__)))
    folder = BASE / SOURCES["evidence"][0]
    with (folder / "point_evidence.csv").open(encoding="utf-8", newline="") as handle:
        points = list(csv.DictReader(handle))
    with (folder / "point_case_relations.csv").open(encoding="utf-8", newline="") as handle:
        relations = list(csv.DictReader(handle))
    ids = {r["detection_id"] for r in points}
    if len(points) != 25 or len(ids) != 25 or len(relations) != 207:
        raise ValueError("Unexpected pilot coverage")
    human = defaultdict(list)
    for source in ("human1", "human2"):
        for row in reports[source]["records"]:
            if row["habitat_admission_accepted"] or row["independent_expert_validation"]:
                raise ValueError("Only preliminary notes supported")
            human[row["detection_id"]].append({"source": source, "record": row})
    assistant = {r["detection_id"]: r for r in reports["assistant"]["records"]}
    if len(human) != 6 or len(assistant) != 19 or set(human) & set(assistant):
        raise ValueError("Note provenance coverage mismatch")
    if set(human) | set(assistant) != ids:
        raise ValueError("Missing or extra point notes")
    cases = defaultdict(set)
    for row in relations:
        if row["detection_id"] not in ids or row["daily_observation_status"] != "unknown":
            raise ValueError("Invalid case relation")
        cases[row["review_unit_id"]].add(row["detection_id"])
    if len(cases) != 21:
        raise ValueError("Unexpected case coverage")
    records = []
    for point in points:
        identity = point["detection_id"]
        if point["target"] or point["natural_forest_shrub_admission"] != "undecided":
            raise ValueError("Admission must remain closed")
        note = assistant.get(identity)
        questions = ["time_matched_natural_vs_managed_cover", "spatial_scope_rule_not_selected"]
        if point["residual_bowtie"] == "True":
            questions.append("native_location_bowtie_uncertainty")
        if not human.get(identity):
            questions.append("researcher_visual_note_pending")
        records.append(
            {
                "detection_id": identity,
                "code": note["code"]
                if note
                else {
                    "SNPP_815579_4958": "A",
                    "SNPP_815579_17606": "B",
                    "SNPP_815579_146808": "C",
                    "N20_815590_159856": "D",
                    "N20_815590_196908": "E",
                    "N20_815590_33762": "F",
                }[identity],
                "human_note_history": human.get(identity, []),
                "assistant_note": note,
                "reference_cover_2017": point["center_cover_group_2017"],
                "open_questions": questions,
                "linked_review_units": sorted(
                    k for k, members in cases.items() if identity in members
                ),
                "habitat_admission": "undecided",
                "target": None,
                "daily_observation_status": "unknown",
                "positive_label_permitted": False,
                "negative_label_permitted": False,
                "automatic_exclusion": False,
            }
        )
    summaries = [
        {
            "review_unit_id": k,
            "point_ids": sorted(members),
            "points_with_human_notes": len(members & set(human)),
            "habitat_admission": "undecided",
        }
        for k, members in sorted(cases.items())
    ]
    result = {
        "version": "habitat_decision_queue_v1",
        "records": records,
        "cases": summaries,
        "point_count": len(records),
        "review_unit_count": len(cases),
        "human_note_points": len(human),
        "human_note_records": sum(map(len, human.values())),
        "assistant_only_points": len(assistant),
        "new_researcher_reviews": 0,
        "source_sha256": pins,
        "labels_created": 0,
        "final_merge_performed": False,
    }
    out = (
        BASE
        / "habitat_decision_queue_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if json.loads(path.read_text(encoding="utf-8")) != result:
        raise ValueError("Output readback mismatch")
    for filename, digest in pins.items():
        pin(ROOT / filename, digest)
    print(out.relative_to(ROOT))
    print("SHA", sha(path))
    print("SOURCE_PINS", len(pins))
    print("CASES_WITH_HUMAN_NOTES", sum(s["points_with_human_notes"] > 0 for s in summaries))
    print("MULTIPOINT_CASES", sum(len(s["point_ids"]) > 1 for s in summaries))


if __name__ == "__main__":
    main()
