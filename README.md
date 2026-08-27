# NetSage AI

## AI-Assisted Network Troubleshooting

NetSage AI is a simple network troubleshooting assistant built for Cisco-style networking lab problems.

The project helps identify possible network issues from a given symptom and network evidence. It combines rule-based checks with AI-based diagnosis and keeps a human reviewer in the loop before a fix is accepted.

## What the Project Does

A network troubleshooting case is given to the system with information such as:

- Network symptom
- Topology details
- Cisco show-command output
- Expected fault
- Network issue type

The system then:

1. Checks the network evidence using predefined rules.
2. Sends the case information for AI diagnosis.
3. Identifies the possible root cause.
4. Gives a confidence level and OSI layer.
5. Provides supporting evidence.
6. Suggests the next command or fix.
7. Allows a human reviewer to accept, edit, or reject the diagnosis.
8. Verifies the final decision using network evidence.

## Main Features

- 30 predefined network troubleshooting cases
- VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT and other issues
- Rule-based network checking
- AI-assisted diagnosis
- Root cause identification
- Confidence and OSI layer information
- Evidence-based recommendations
- Human review and correction
- Responsible AI review logging
- Interactive Streamlit dashboard
- Excel-based case and result summaries

## Project Workflow

```text
Network Case
     ↓
Network Evidence
     ↓
Rule Checker
     ↓
AI Diagnosis
     ↓
Human Review
     ↓
Correction / Approval
     ↓
Verification
