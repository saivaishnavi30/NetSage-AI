import os
import json
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Configuration


st.set_page_config(
    page_title="NetSage AI",
    page_icon="🌐",
    layout="wide"
)

load_dotenv()

CASES_FILE = "data/cases.csv"
PIPELINE_FILE = "outputs/pipeline_results.csv"
REVIEW_FILE = "review/responsible_ai_log.csv"
PROMPT_FILE = "prompts/diagnose_prompt.md"

# --------------------------------------------------
# Gemini setup
# --------------------------------------------------

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
]

# --------------------------------------------------
# Load data
# --------------------------------------------------

cases = pd.read_csv(CASES_FILE)
pipeline = pd.read_csv(PIPELINE_FILE)
review = pd.read_csv(REVIEW_FILE)

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# --------------------------------------------------
# AI diagnosis function
# --------------------------------------------------

def run_ai_diagnosis(case):

    if client is None:
        return {
            "error": "GEMINI_API_KEY not found."
        }

    case_text = f"""
CASE ID: {case['case_id']}

ISSUE TYPE:
{case['issue_type']}

SYMPTOM:
{case['symptom']}

TOPOLOGY NOTE:
{case['topology_note']}

SHOW COMMAND OUTPUT:
{case['show_outputs']}

EXPECTED FAULT:
{case['expected_fault']}

EXPECTED OSI LAYER:
{case['osi_layer']}

CONCEPT:
{case['concept']}

SEVERITY:
{case['severity']}
"""

    full_prompt = f"""
{system_prompt}

Now diagnose the following network troubleshooting case.

{case_text}

Return ONLY valid JSON.
"""

    last_error = None

    for model in MODELS:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt
                )

                text = response.text.strip()

                if text.startswith("```json"):
                    text = text[7:]

                if text.startswith("```"):
                    text = text[3:]

                if text.endswith("```"):
                    text = text[:-3]

                text = text.strip()

                diagnosis = json.loads(text)

                return diagnosis

            except Exception as e:

                last_error = str(e)

                if attempt == 0:
                    time.sleep(3)

    return {
        "error": (
            "Gemini is temporarily unavailable. "
            "Please try again shortly."
        ),
        "details": last_error
    }


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🌐 NetSage AI")

st.subheader(
    "AI-Assisted Network Troubleshooting & Responsible AI Review"
)

st.markdown(
    """
NetSage AI analyzes Cisco-style networking problems using
**deterministic rule checks + AI-assisted diagnosis**.

> ⚠️ Human review is required before accepting a diagnosis
> or applying a configuration change.
"""
)

st.divider()

# --------------------------------------------------
# Metrics
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cases", len(cases))

with col2:
    st.metric("Human Reviewed", len(review))

with col3:
    edited = (
        review["human_decision"]
        .astype(str)
        .str.lower()
        .eq("edited")
        .sum()
    )

    st.metric("AI Corrections", edited)

with col4:
    st.metric(
        "Issue Types",
        cases["issue_type"].nunique()
    )

st.divider()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.header("🔎 Case Selection")

selected_case = st.sidebar.selectbox(
    "Select troubleshooting case",
    cases["case_id"].tolist()
)

case = cases[
    cases["case_id"] == selected_case
].iloc[0]

pipeline_case = pipeline[
    pipeline["case_id"] == selected_case
].iloc[0]

# --------------------------------------------------
# Case Information
# --------------------------------------------------

st.header(f"Case: {selected_case}")

c1, c2, c3 = st.columns(3)

with c1:
    st.write("**Issue Type**")
    st.info(str(case["issue_type"]))

with c2:
    st.write("**Severity**")
    st.warning(str(case["severity"]))

with c3:
    st.write("**OSI Layer**")
    st.success(str(case["osi_layer"]))

# --------------------------------------------------
# Symptom
# --------------------------------------------------

st.subheader("🔎 Symptom")

st.write(str(case["symptom"]))

# --------------------------------------------------
# Topology
# --------------------------------------------------

st.subheader("🗺️ Topology Note")

st.write(str(case["topology_note"]))

# --------------------------------------------------
# Show Evidence
# --------------------------------------------------

st.subheader("💻 Show-Command Evidence")

st.code(
    str(case["show_outputs"]),
    language="text"
)

# --------------------------------------------------
# Rule Checker
# --------------------------------------------------

st.subheader("🛡️ Deterministic Rule Checker")

findings = str(
    pipeline_case["rule_findings"]
)

if findings in ["[]", "", "nan"]:

    st.success(
        "No deterministic configuration problems detected."
    )

else:

    st.error(
        "Deterministic configuration findings detected."
    )

    st.write(findings)

# --------------------------------------------------
# Expected Diagnosis
# --------------------------------------------------

st.subheader("🎯 Expected Diagnosis")

st.write(
    f"**Expected Fault:** {case['expected_fault']}"
)

st.write(
    f"**Concept:** {case['concept']}"
)

# --------------------------------------------------
# AI Diagnosis
# --------------------------------------------------

st.subheader("🤖 AI Diagnosis")

st.info(
    "AI output is advisory. Human review is mandatory."
)

if st.button(
    "🚀 Run AI Diagnosis",
    type="primary"
):

    with st.spinner(
        "NetSage AI is analyzing the network evidence..."
    ):

        diagnosis = run_ai_diagnosis(case)

    st.session_state["diagnosis"] = diagnosis

# Display diagnosis if available

if "diagnosis" in st.session_state:

    diagnosis = st.session_state["diagnosis"]

    if "error" in diagnosis:

        st.error(
            diagnosis["error"]
        )

        if "details" in diagnosis:
            with st.expander("Technical details"):
                st.code(
                    str(diagnosis["details"])
                )

    else:

        st.success(
            "AI diagnosis generated successfully."
        )

        st.write(
            "**Root Cause:**"
        )

        st.write(
            diagnosis.get(
                "root_cause",
                "Not provided"
            )
        )

        st.write(
            "**Confidence:**"
        )

        st.write(
            diagnosis.get(
                "confidence",
                "Not provided"
            )
        )

        st.write(
            "**OSI Layer:**"
        )

        st.write(
            diagnosis.get(
                "osi_layer",
                "Not provided"
            )
        )

        st.write(
            "**Evidence:**"
        )

        evidence = diagnosis.get(
            "evidence",
            []
        )

        for item in evidence:
            st.write(f"- {item}")

        st.write(
            "**Recommended Next Command:**"
        )

        st.code(
            diagnosis.get(
                "next_command",
                "Not provided"
            )
        )

        st.write(
            "**Recommended Fix Steps:**"
        )

        fix_steps = diagnosis.get(
            "fix_steps",
            []
        )

        for i, step in enumerate(
            fix_steps,
            start=1
        ):
            st.write(
                f"{i}. {step}"
            )

        st.write(
            "**Verification:**"
        )

        st.write(
            diagnosis.get(
                "verification",
                "Not provided"
            )
        )

# --------------------------------------------------
# Human Review
# --------------------------------------------------

st.divider()

st.subheader("👤 Human Review")

case_review = review[
    review["case_id"] == selected_case
]

if len(case_review) > 0:

    review_row = case_review.iloc[0]

    st.write(
        f"**Previous Human Decision:** "
        f"{review_row['human_decision']}"
    )

    st.write(
        f"**Human Correction:** "
        f"{review_row['human_correction']}"
    )

    st.write(
        f"**Reason:** "
        f"{review_row['reason']}"
    )

else:

    st.info(
        "No previous human-review record exists for this case."
    )

st.markdown(
    "### Review Decision"
)

review_decision = st.radio(
    "Human reviewer decision",
    [
        "Accept",
        "Edit",
        "Reject"
    ],
    horizontal=True
)

if review_decision == "Edit":

    st.text_area(
        "Human correction",
        placeholder="Enter the corrected diagnosis or recommendation..."
    )

elif review_decision == "Reject":

    st.warning(
        "The AI recommendation will not be accepted."
    )

else:

    st.success(
        "Reviewer accepts the AI recommendation."
    )

# --------------------------------------------------
# Verification
# --------------------------------------------------

st.subheader("✅ Verification")

st.write(
    """
After reviewing the recommendation, the engineer should
apply the approved fix in the network lab and rerun the
relevant show commands and connectivity tests.
"""
)

human_confirm = st.checkbox(
    "Human reviewer confirms diagnosis before applying fix"
)

fix_verified = st.checkbox(
    "Fix verified using network evidence"
)

if human_confirm and fix_verified:

    st.success(
        "✓ Human review and verification completed."
    )

# --------------------------------------------------
# Charts
# --------------------------------------------------

st.divider()

st.header("📊 Network Troubleshooting Overview")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:

    st.subheader("Cases by Issue Type")

    issue_counts = (
        cases["issue_type"]
        .value_counts()
    )

    st.bar_chart(issue_counts)

with chart_col2:

    st.subheader("Cases by Severity")

    severity_counts = (
        cases["severity"]
        .value_counts()
    )

    st.bar_chart(severity_counts)

# --------------------------------------------------
# Responsible AI
# --------------------------------------------------

st.divider()

st.header("🤝 Responsible AI Summary")

accepted = (
    review["human_decision"]
    .astype(str)
    .str.lower()
    .eq("accepted")
    .sum()
)

edited = (
    review["human_decision"]
    .astype(str)
    .str.lower()
    .eq("edited")
    .sum()
)

rejected = (
    review["human_decision"]
    .astype(str)
    .str.lower()
    .eq("rejected")
    .sum()
)

r1, r2, r3 = st.columns(3)

with r1:
    st.metric(
        "Accepted",
        accepted
    )

with r2:
    st.metric(
        "Edited",
        edited
    )

with r3:
    st.metric(
        "Rejected",
        rejected
    )

st.caption(
    "NetSage AI uses a human-in-the-loop troubleshooting workflow."
)
