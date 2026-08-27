import os
import re
import json
import pandas as pd

CASES_FILE = "data/cases.csv"
REVIEW_FILE = "review/responsible_ai_log.csv"

OUTPUT_CSV = "outputs/pipeline_results.csv"
OUTPUT_JSON = "outputs/pipeline_results.json"


def text_rule_checks(case):
    """
    Deterministic checks based only on the supplied
    symptom, topology note and show-command evidence.
    """

    text = " ".join([
        str(case.get("symptom", "")),
        str(case.get("topology_note", "")),
        str(case.get("show_outputs", ""))
    ]).lower()

    findings = []

    # Duplicate IP
    if (
        ("duplicate ip" in text)
        or ("duplicate address" in text)
        or ("same ip" in text)
    ):
        findings.append("Duplicate IP detected")

    # Wrong mask
    if (
        ("wrong mask" in text)
        or ("incorrect mask" in text)
        or ("subnet mask" in text and "mismatch" in text)
    ):
        findings.append("Possible wrong subnet mask")

    # Gateway mismatch
    if (
        ("gateway mismatch" in text)
        or ("wrong gateway" in text)
        or ("default gateway" in text and "incorrect" in text)
    ):
        findings.append("Gateway mismatch detected")

    # Interface down
    if (
        ("administratively down" in text)
        or ("interface down" in text)
        or ("line protocol is down" in text)
        or ("shutdown" in text)
    ):
        findings.append("Interface-down condition detected")

    # Missing VLAN
    if (
        ("missing vlan" in text)
        or ("vlan does not exist" in text)
        or ("vlan is not created" in text)
        or ("vlan not allowed" in text)
    ):
        findings.append("Possible missing/misconfigured VLAN")

    # Missing route
    if (
        ("missing route" in text)
        or ("no route" in text)
        or ("network is unreachable" in text)
        or ("route is missing" in text)
    ):
        findings.append("Possible missing route")

    return findings


def main():

    print("=" * 70)
    print("NetSage AI - Integrated Troubleshooting Pipeline")
    print("=" * 70)

    # --------------------------------------------------
    # Load cases
    # --------------------------------------------------

    cases = pd.read_csv(CASES_FILE)

    print(f"Loaded cases: {len(cases)}")

    # --------------------------------------------------
    # Load responsible AI review log
    # --------------------------------------------------

    if os.path.exists(REVIEW_FILE):
        review = pd.read_csv(REVIEW_FILE)
        review_lookup = {
            row["case_id"]: row.to_dict()
            for _, row in review.iterrows()
        }
    else:
        review_lookup = {}

    # --------------------------------------------------
    # Process every case
    # --------------------------------------------------

    results = []

    for _, case in cases.iterrows():

        findings = text_rule_checks(case)

        case_id = case["case_id"]

        review_info = review_lookup.get(case_id, {})

        result = {
            "case_id": case_id,
            "issue_type": case["issue_type"],
            "severity": case["severity"],
            "symptom": case["symptom"],
            "expected_fault": case["expected_fault"],
            "osi_layer": case["osi_layer"],
            "concept": case["concept"],

            "rule_findings": findings,
            "rule_problem_count": len(findings),

            # AI will be filled by the AI diagnosis stage
            "ai_status": "PENDING",

            # Human review information
            "human_reviewed": bool(review_info),

            "human_decision": review_info.get(
                "human_decision",
                ""
            ),

            "human_correction": review_info.get(
                "human_correction",
                ""
            )
        }

        results.append(result)

    # --------------------------------------------------
    # Save CSV
    # --------------------------------------------------

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    # --------------------------------------------------
    # Save JSON
    # --------------------------------------------------

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    total_cases = len(results)

    cases_with_rule_findings = sum(
        r["rule_problem_count"] > 0
        for r in results
    )

    reviewed_cases = sum(
        r["human_reviewed"]
        for r in results
    )

    print()
    print("PIPELINE SUMMARY")
    print("-" * 70)

    print(f"Total cases              : {total_cases}")
    print(
        f"Cases with rule findings : "
        f"{cases_with_rule_findings}"
    )
    print(
        f"Human-reviewed cases     : "
        f"{reviewed_cases}"
    )

    print()
    print("Outputs created:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_JSON}")

    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
