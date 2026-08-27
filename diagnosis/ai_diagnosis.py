import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
]

# Load diagnosis prompt
with open("prompts/diagnose_prompt.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Load dataset
cases = pd.read_csv("data/cases.csv")

# First test case
case = cases.iloc[0]

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

Now diagnose this network troubleshooting case.

{case_text}

Return ONLY valid JSON.
"""

print("Running NetSage AI diagnosis...")
print("-" * 60)

response = None
last_error = None

for model in MODELS:
    for attempt in range(2):
        try:
            print(f"Trying model: {model} (attempt {attempt + 1})")

            interaction = client.interactions.create(
                model=model,
                input=full_prompt
            )

            text = interaction.output_text.strip()

            response = text

            print(f"SUCCESS with {model}")
            break

        except Exception as e:
            last_error = e
            print(f"Model unavailable: {model}")
            print("Retrying...")

            if attempt == 0:
                time.sleep(5)

    if response:
        break

if not response:
    print("-" * 60)
    print("ERROR: All Gemini models were temporarily unavailable.")
    print(last_error)
    raise SystemExit(1)

# Remove markdown JSON fences if present
if response.startswith("```json"):
    response = response[7:]

if response.startswith("```"):
    response = response[3:]

if response.endswith("```"):
    response = response[:-3]

response = response.strip()

try:
    diagnosis = json.loads(response)

except json.JSONDecodeError:
    print("-" * 60)
    print("ERROR: Gemini returned invalid JSON.")
    print(response)
    raise SystemExit(1)

print("-" * 60)
print(json.dumps(diagnosis, indent=2))

# Save diagnosis
os.makedirs("outputs", exist_ok=True)

result = {
    "case_id": case["case_id"],
    "issue_type": case["issue_type"],
    "diagnosis": diagnosis
}

with open(
    "outputs/diagnosis_results.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(result, f, indent=2)

print("-" * 60)
print("SUCCESS!")
print("Diagnosis saved to:")
print("outputs/diagnosis_results.json")
