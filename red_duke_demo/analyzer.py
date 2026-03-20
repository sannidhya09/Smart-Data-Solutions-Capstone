#!/usr/bin/env python3
"""
RED DUKE — AI Document Analyzer
=================================
Uses Google Gemini to deeply analyze parsed documents against the
SDS custom implementation standard and produce structured intelligence
for the React dashboard.

Author: Sannidhya Tiwari
"""

import json
import os
import subprocess
import sys

# ══════════════════════════════════════════════════════════════════════════════
# SDS CUSTOM IMPLEMENTATION STANDARD
# Stage gates mirror the SDS delivery lifecycle: TG-1 → TG0 → TG1 → TG2 → TG3
# ══════════════════════════════════════════════════════════════════════════════

SDS_STANDARD = {
    "TG-1 (Initiation)": [
        {"deliverable": "Business Requirements Document (BRD)", "responsibility": "Business Analyst"},
        {"deliverable": "High-Level Project Plan / Critical Path", "responsibility": "PM"},
        {"deliverable": "Client Kickoff / Scope Presentation", "responsibility": "PM"},
        {"deliverable": "Security & Access Control Documentation", "responsibility": "Engineering"},
        {"deliverable": "Training & Process Awareness Documentation", "responsibility": "PM"},
    ],
    "TG0 (Design)": [
        {"deliverable": "Workflow / Process Flow Diagram", "responsibility": "Engineering"},
        {"deliverable": "Data Mapping Document", "responsibility": "Engineering"},
        {"deliverable": "Technical Design Specification", "responsibility": "Engineering"},
        {"deliverable": "BRD Sign-off", "responsibility": "Business Analyst / PM"},
    ],
    "TG1 (Implementation)": [
        {"deliverable": "Implementation / Transition Workbook", "responsibility": "PM / Engineering"},
        {"deliverable": "Configuration Documentation", "responsibility": "Engineering"},
        {"deliverable": "Reporting Requirements & SLA Documentation", "responsibility": "PM"},
        {"deliverable": "Mailroom / Workflow Configuration", "responsibility": "Engineering"},
        {"deliverable": "Eligibility & Claims Configuration", "responsibility": "Engineering"},
    ],
    "TG2 (Test)": [
        {"deliverable": "UAT Plan & Test Cases", "responsibility": "Engineering / PM"},
        {"deliverable": "UAT Sign-off / Testing Evidence", "responsibility": "Engineering"},
        {"deliverable": "TPM / Compliance Checklist", "responsibility": "PM / Engineer"},
        {"deliverable": "Functional & Volume Testing Evidence", "responsibility": "Engineering"},
    ],
    "TG3 (Deploy/Warranty)": [
        {"deliverable": "M2P / Go-Live Sign-off", "responsibility": "PM / Tech Lead"},
        {"deliverable": "Post-Go-Live Warranty Checklist", "responsibility": "PM"},
        {"deliverable": "Lessons Learned Document", "responsibility": "PM"},
        {"deliverable": "Final Client Documentation Handoff", "responsibility": "PM"},
    ],
}

GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_CHARS_PER_DOC = 10000  # Per-document text cap to control cost


# ══════════════════════════════════════════════════════════════════════════════
# GEMINI CLIENT  (uses the new google-genai SDK)
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_genai():
    try:
        from google import genai  # noqa: F401
    except ImportError:
        print("  Installing google-genai ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "google-genai"]
        )


def get_client():
    _ensure_genai()
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
    return genai.Client(api_key=api_key)


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_prompt(parse_results: list) -> str:
    doc_sections = []
    for r in parse_results:
        if not r.success:
            doc_sections.append(
                f"=== DOCUMENT: {r.filename} ===\nSTATUS: PARSE FAILED — {r.error}\n"
            )
            continue

        snippet = r.text[:MAX_CHARS_PER_DOC]
        doc_sections.append(
            f"=== DOCUMENT: {r.filename} ===\n"
            f"Type: {r.file_type}\n"
            f"Size: {r.file_size / 1024:.1f} KB\n"
            f"Sections: {len(r.sections)}  |  Tables: {len(r.tables)}\n"
            f"Content:\n{snippet}\n"
        )

    documents_text = "\n".join(doc_sections)
    standard_json = json.dumps(SDS_STANDARD, indent=2)
    n_docs = len(parse_results)
    n_parsed = sum(1 for r in parse_results if r.success)

    return f"""You are an expert implementation documentation analyst at Smart Data Solutions (SDS), a healthcare data processing and mailroom services company.

You have been given {n_docs} documents ({n_parsed} successfully parsed) from a client SharePoint implementation folder. Your job is to:
1. Deeply understand what each document contains
2. Map evidence to the SDS stage-gate delivery standard
3. Identify what is present, what is missing, and what gaps pose risk
4. Produce a plain-language narrative of the client's workflow

SDS IMPLEMENTATION STANDARD (Stage Gates & Required Deliverables):
{standard_json}

CLIENT DOCUMENTS:
{documents_text}

Analyze thoroughly, then return ONLY a single valid JSON object with EXACTLY this structure (no markdown fences, no extra text):

{{
  "client_overview": {{
    "client_name": "infer from documents, or use 'SDS Client'",
    "summary": "2-3 sentence plain-language summary of this client implementation and what is being set up",
    "scope": "concise description of services and systems being implemented",
    "integrations": ["list every system, tool, or integration mentioned"],
    "key_decisions": ["list important decisions that have been documented or made"],
    "open_risks": ["list risks, concerns, or unresolved items found in the documents"],
    "current_phase": "estimated current project phase based on the evidence (e.g. Implementation/TG1)"
  }},
  "documents": [
    {{
      "filename": "exact filename",
      "file_type": "file type string",
      "purpose": "one sentence: what is the purpose of this document",
      "summary": "2-3 sentences describing what this document actually contains",
      "key_topics": ["topic1", "topic2", "topic3"],
      "artifacts_present": ["what implementation evidence or proof this document provides"],
      "artifacts_missing_or_incomplete": ["what appears TBD, blank, missing, or incomplete within this document"]
    }}
  ],
  "workflow_narrative": "Write 3-5 paragraphs describing the end-to-end client workflow as evidenced by ALL the documents combined. Use plain language suitable for a new PM or engineer. Reference document names as sources. Describe the flow from intake/mailroom through processing, eligibility, and output/export.",
  "checklist": [
    {{
      "deliverable": "exact deliverable name from the SDS standard above",
      "stage_gate": "exact stage gate name from the SDS standard",
      "responsibility": "role from the SDS standard",
      "status": "PRESENT if clear evidence exists, PARTIAL if mentioned but incomplete, MISSING if no evidence found",
      "evidence_files": ["list filenames that provide evidence — empty array if MISSING"],
      "confidence": "HIGH if strong direct evidence, MEDIUM if inferred, LOW if uncertain",
      "notes": "1-2 sentence explanation of why this status was assigned"
    }}
  ],
  "gap_analysis": [
    {{
      "gap": "specific description of what documentation or evidence is missing or insufficient",
      "impact": "HIGH if blocks a stage gate or compliance requirement, MEDIUM if creates risk, LOW if nice-to-have",
      "stage_gate": "which stage gate this gap affects",
      "recommendation": "specific actionable step to close this gap",
      "responsible_party": "who at SDS should address this"
    }}
  ],
  "metrics": {{
    "total_documents": {n_docs},
    "successfully_parsed": {n_parsed},
    "coverage_score": 0,
    "total_gaps": 0,
    "high_risk_gaps": 0,
    "stage_gate_completion": {{
      "TG-1": 0,
      "TG0": 0,
      "TG1": 0,
      "TG2": 0,
      "TG3": 0
    }}
  }}
}}

IMPORTANT INSTRUCTIONS:
- Fill ALL metrics fields with real integers (0-100 for percentages, counts for totals)
- coverage_score = percentage of SDS standard deliverables that have PRESENT or PARTIAL status
- total_gaps = total count of items in gap_analysis array
- high_risk_gaps = count of gap_analysis items where impact is HIGH
- stage_gate_completion values = percentage of that gate's deliverables that are PRESENT or PARTIAL
- The checklist must include ALL {sum(len(v) for v in SDS_STANDARD.values())} deliverables from the SDS standard — do not skip any
- Return ONLY the JSON object. No markdown. No explanation before or after."""


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def analyze_documents(parse_results: list) -> dict:
    """
    Run Gemini analysis over all parsed documents.
    Returns the structured analysis dict ready for JSON serialisation.
    """
    print(f"  Model: {GEMINI_MODEL}")

    client = get_client()
    prompt = build_prompt(parse_results)
    print(f"  Prompt size: {len(prompt):,} characters")

    from google.genai import types

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    analysis = json.loads(raw)

    # Coerce all metric values to int (Gemini sometimes returns strings)
    metrics = analysis.get("metrics", {})
    for key in ("coverage_score", "total_gaps", "high_risk_gaps", "total_documents", "successfully_parsed"):
        if key in metrics:
            try:
                metrics[key] = int(metrics[key])
            except (ValueError, TypeError):
                metrics[key] = 0

    sg = metrics.get("stage_gate_completion", {})
    for k in list(sg.keys()):
        try:
            sg[k] = int(sg[k])
        except (ValueError, TypeError):
            sg[k] = 0

    # If Gemini returned zeros for computed metrics, calculate them ourselves
    checklist = analysis.get("checklist", [])
    if metrics.get("coverage_score", 0) == 0 and checklist:
        present = sum(1 for c in checklist if c.get("status") in ("PRESENT", "PARTIAL"))
        metrics["coverage_score"] = round(present / len(checklist) * 100)

    gaps = analysis.get("gap_analysis", [])
    if metrics.get("total_gaps", 0) == 0:
        metrics["total_gaps"] = len(gaps)
    if metrics.get("high_risk_gaps", 0) == 0:
        metrics["high_risk_gaps"] = sum(1 for g in gaps if g.get("impact") == "HIGH")

    # Recompute stage-gate completion if all zeros
    if all(v == 0 for v in sg.values()) and checklist:
        for gate_label, gate_items in SDS_STANDARD.items():
            short = gate_label.split(" ")[0]  # e.g. "TG-1"
            gate_deliverables = [i["deliverable"] for i in gate_items]
            gate_checklist = [
                c for c in checklist
                if c.get("deliverable") in gate_deliverables
            ]
            if gate_checklist:
                present = sum(1 for c in gate_checklist if c.get("status") in ("PRESENT", "PARTIAL"))
                sg[short] = round(present / len(gate_checklist) * 100)

    analysis["metrics"] = metrics
    return analysis
