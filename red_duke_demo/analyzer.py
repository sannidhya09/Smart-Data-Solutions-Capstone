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

    return f"""You are RED DUKE, an expert implementation documentation analyst at Smart Data Solutions (SDS).
SDS is a healthcare technology company that automates complex payer operations — digital mailroom, document intelligence, claims processing, and interoperability — for 500+ healthcare organizations.

You have {n_docs} documents ({n_parsed} parsed) from a client implementation folder. Your mission:
1. Deeply understand what EACH document contains — read between the lines, note placeholders/TBDs
2. Cross-reference documents against each other (e.g. does the BRD align with the project plan?)
3. Map evidence to the SDS stage-gate standard below
4. Identify gaps, prioritize them by business risk, and give concrete next steps
5. Produce a workflow narrative that a new PM could use on day one

SDS IMPLEMENTATION STANDARD (Stage Gates & Required Deliverables):
{standard_json}

CLIENT DOCUMENTS:
{documents_text}

Return ONLY a single valid JSON object (no markdown fences, no extra text) with EXACTLY this structure:

{{
  "client_overview": {{
    "client_name": "Smart Data Solutions",
    "summary": "2-3 sentences summarizing what this implementation project is setting up, what type of client engagement this is, and where it currently stands. Be specific — mention document types, mailroom configuration, data flows.",
    "scope": "concise description of services and systems being implemented",
    "integrations": ["every system, tool, platform, or integration mentioned across ALL documents"],
    "key_decisions": ["important decisions documented or implied — include WHO decided and WHEN if available"],
    "open_risks": ["risks, blockers, or unresolved items — be specific about what could go wrong and the business impact"],
    "current_phase": "estimated current stage gate based on evidence (e.g. TG0 (Design))"
  }},
  "documents": [
    {{
      "filename": "exact filename",
      "file_type": "file type string",
      "purpose": "one sentence: what is the purpose of this document",
      "summary": "2-3 sentences describing what this document actually contains — mention specific data points, not just topics",
      "key_topics": ["topic1", "topic2", "topic3"],
      "artifacts_present": ["specific evidence this document provides — quote section names or data points"],
      "artifacts_missing_or_incomplete": ["what appears TBD, blank, placeholder, or incomplete — be specific about WHAT is missing"],
      "cross_references": ["how this document relates to or depends on other documents in the set"],
      "quality_score": "STRONG if thorough and complete, ADEQUATE if usable but has gaps, WEAK if mostly placeholder/draft",
      "quality_numeric": 0
    }}
  ],
  "workflow_narrative": "Write 4-6 paragraphs. Paragraph 1: Overview of the client engagement and what SDS is delivering. Paragraph 2: Describe the document intake and mailroom flow. Paragraph 3: Describe data processing, classification, and routing. Paragraph 4: Describe reporting, SLAs, and output delivery. Paragraph 5: Current state assessment — what is ready, what is not, and what the critical path forward looks like. Reference specific document names as sources throughout.",
  "checklist": [
    {{
      "deliverable": "exact deliverable name from the SDS standard above",
      "stage_gate": "exact stage gate name from the SDS standard",
      "responsibility": "role from the SDS standard",
      "status": "PRESENT if clear evidence exists, PARTIAL if mentioned but incomplete/draft, MISSING if no evidence found",
      "evidence_files": ["list filenames that provide evidence — empty array if MISSING"],
      "confidence": "HIGH if strong direct evidence, MEDIUM if inferred from context, LOW if uncertain",
      "notes": "2-3 sentences: WHY this status was assigned, WHAT specific evidence was found or is lacking, and WHAT needs to happen to move this to PRESENT",
      "priority": "P1 if blocks next stage gate, P2 if needed within 2 weeks, P3 if can be deferred",
      "estimated_effort": "Small (< 1 day), Medium (1-3 days), or Large (3+ days) to complete this deliverable",
      "is_blocker": true,
      "evidence_trail": [
        {{
          "source_file": "exact filename where evidence was found",
          "section_or_location": "heading, sheet name, slide number, or page where the evidence appears (e.g. 'Sheet: Data Mapping', 'Slide 4', 'Section: Requirements')",
          "excerpt": "verbatim quote (30-80 words) from the document that constitutes the evidence — copy the exact text, do NOT paraphrase",
          "assessment": "1-2 sentences: what this excerpt proves or fails to prove about the deliverable, and what is still missing"
        }}
      ]
    }}
  ],
  "gap_analysis": [
    {{
      "gap": "specific description of what is missing — not generic, reference actual document content or absence",
      "impact": "HIGH if blocks a stage gate or compliance, MEDIUM if creates operational risk, LOW if nice-to-have",
      "stage_gate": "which stage gate this gap affects",
      "recommendation": "concrete, actionable step — name the document to create, the meeting to schedule, or the sign-off to obtain",
      "responsible_party": "specific role at SDS who should own this",
      "estimated_effort": "Small (< 1 day), Medium (1-3 days), or Large (3+ days)",
      "dependencies": ["list any other gaps or deliverables that must be resolved first"]
    }}
  ],
  "action_items": [
    {{
      "action": "specific task description — actionable and concrete",
      "owner": "role responsible",
      "priority": "P1/P2/P3",
      "stage_gate": "which gate this supports",
      "deliverable": "which checklist deliverable this helps complete",
      "estimated_effort": "Small/Medium/Large"
    }}
  ],
  "readiness_assessment": {{
    "overall_readiness": "RED/YELLOW/GREEN — overall project readiness to advance",
    "next_gate": "which stage gate the project should be working toward",
    "blockers_to_advance": ["specific items that MUST be completed before advancing to the next gate"],
    "quick_wins": ["items that could be completed quickly to improve coverage score"],
    "executive_summary": "3-4 sentences a VP could read to understand project health, key risks, and recommended next steps"
  }},
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

CRITICAL INSTRUCTIONS:
- Fill ALL metrics with real integers (0-100 for percentages, counts for totals)
- coverage_score = percentage of deliverables with PRESENT or PARTIAL status
- The checklist MUST include ALL {sum(len(v) for v in SDS_STANDARD.values())} deliverables — do not skip any
- action_items should be ordered by priority (P1 first), max 15 items
- Be specific and actionable — avoid generic statements like "needs more documentation"
- Cross-reference documents: if Document A mentions something that Document B should detail, note the connection
- EVIDENCE TRAIL: For EVERY checklist item with status PRESENT or PARTIAL, you MUST include at least one evidence_trail entry with a verbatim excerpt (direct quote) from the source document. For MISSING items, include an empty evidence_trail array []. This is critical for enterprise trust — every conclusion must be traceable to source text.
- quality_numeric: For each document, provide a quality score 0-100 (0=empty/useless, 25=mostly placeholder, 50=draft with some content, 75=solid working document, 100=production-ready and complete). This powers the multi-dimensional scoring engine.
- is_blocker: set to true if this deliverable MUST be completed before the stage gate can be passed (i.e. it's a hard requirement, not optional). Set to false for nice-to-have or supplementary items.
- Return ONLY the JSON object. No markdown. No explanation."""


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

    # Handle "Extra data" — Gemini sometimes returns multiple JSON objects.
    # Use JSONDecoder to parse only the first valid object.
    decoder = json.JSONDecoder()
    analysis, _ = decoder.raw_decode(raw)

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

    # ── Go / No-Go Decision Engine ──
    # Deterministic: computed from checklist data, not another AI call
    analysis["gate_decisions"] = _compute_gate_decisions(checklist, gaps)

    return analysis


def _compute_gate_decisions(checklist: list, gaps: list) -> dict:
    """
    Compute a Go/No-Go recommendation for each stage gate.
    Returns a dict keyed by gate short name (TG-1, TG0, etc.).

    Decision logic:
      - GO:      all blockers PRESENT, confidence >= 70%, no HIGH gaps
      - CONDITIONAL: some blockers PARTIAL or confidence 50-69%
      - NO-GO:   any blocker MISSING, confidence < 50%, or HIGH gaps remain
    """
    gate_decisions = {}

    for gate_label, gate_items in SDS_STANDARD.items():
        short = gate_label.split(" ")[0]  # TG-1, TG0, etc.
        gate_deliverables = {i["deliverable"] for i in gate_items}

        # Get checklist items for this gate
        gate_checklist = [
            c for c in checklist
            if c.get("deliverable") in gate_deliverables
        ]

        if not gate_checklist:
            gate_decisions[short] = _empty_gate_decision(gate_label)
            continue

        # Classify items
        total = len(gate_checklist)
        present_items = [c for c in gate_checklist if c.get("status") == "PRESENT"]
        partial_items = [c for c in gate_checklist if c.get("status") == "PARTIAL"]
        missing_items = [c for c in gate_checklist if c.get("status") == "MISSING"]

        # Blockers: items marked is_blocker=true, OR P1 priority items
        blocker_items = [
            c for c in gate_checklist
            if c.get("is_blocker") is True or c.get("priority") == "P1"
        ]
        blockers_met = [b for b in blocker_items if b.get("status") == "PRESENT"]
        blockers_partial = [b for b in blocker_items if b.get("status") == "PARTIAL"]
        blockers_missing = [b for b in blocker_items if b.get("status") == "MISSING"]

        # Optional gaps: non-blocker items that are missing/partial
        optional_gaps = [
            c for c in gate_checklist
            if c not in blocker_items and c.get("status") != "PRESENT"
        ]

        # Confidence: weighted score based on item confidence levels
        confidence_map = {"HIGH": 100, "MEDIUM": 65, "LOW": 30}
        confidence_values = [
            confidence_map.get(c.get("confidence", "LOW"), 30)
            for c in gate_checklist
        ]
        confidence_score = round(sum(confidence_values) / len(confidence_values)) if confidence_values else 0

        # HIGH gaps for this gate
        gate_high_gaps = [
            g for g in gaps
            if g.get("impact") == "HIGH" and g.get("stage_gate", "") == gate_label
        ]

        # Completion percentage
        completion = round((len(present_items) + 0.5 * len(partial_items)) / total * 100) if total else 0

        # ── Decision logic ──
        if blockers_missing:
            decision = "NO-GO"
            risk = "HIGH"
        elif gate_high_gaps:
            decision = "NO-GO"
            risk = "HIGH"
        elif confidence_score < 50:
            decision = "NO-GO"
            risk = "HIGH"
        elif blockers_partial:
            decision = "CONDITIONAL"
            risk = "MEDIUM"
        elif confidence_score < 70:
            decision = "CONDITIONAL"
            risk = "MEDIUM"
        elif optional_gaps:
            decision = "CONDITIONAL"
            risk = "LOW"
        else:
            decision = "GO"
            risk = "LOW"

        # Estimated delay
        if decision == "NO-GO":
            large = sum(1 for c in blockers_missing if c.get("estimated_effort", "").startswith("Large"))
            medium = sum(1 for c in blockers_missing if c.get("estimated_effort", "").startswith("Medium"))
            if large > 0:
                delay = f"{large * 3 + medium}-{large * 5 + medium * 3} weeks"
            elif medium > 0:
                delay = f"{medium}-{medium * 3} weeks"
            else:
                delay = "1-2 weeks"
        elif decision == "CONDITIONAL":
            delay = "0-1 weeks (if conditions met)"
        else:
            delay = "None"

        gate_decisions[short] = {
            "gate": gate_label,
            "decision": decision,
            "confidence_score": confidence_score,
            "risk_severity": risk,
            "completion_pct": completion,
            "total_deliverables": total,
            "present_count": len(present_items),
            "partial_count": len(partial_items),
            "missing_count": len(missing_items),
            "blockers": [
                {
                    "deliverable": b.get("deliverable", ""),
                    "status": b.get("status", ""),
                    "owner": b.get("responsibility", ""),
                    "effort": b.get("estimated_effort", ""),
                    "notes": b.get("notes", ""),
                }
                for b in blocker_items
            ],
            "blockers_met": len(blockers_met),
            "blockers_remaining": len(blockers_partial) + len(blockers_missing),
            "optional_gaps": [
                {
                    "deliverable": o.get("deliverable", ""),
                    "status": o.get("status", ""),
                    "effort": o.get("estimated_effort", ""),
                }
                for o in optional_gaps
            ],
            "high_risk_gaps": [g.get("gap", "") for g in gate_high_gaps],
            "suggested_delay": delay,
            "rationale": _build_rationale(decision, blockers_missing, blockers_partial, gate_high_gaps, confidence_score, optional_gaps),
        }

    return gate_decisions


def _empty_gate_decision(gate_label: str) -> dict:
    return {
        "gate": gate_label,
        "decision": "NO-GO",
        "confidence_score": 0,
        "risk_severity": "HIGH",
        "completion_pct": 0,
        "total_deliverables": 0,
        "present_count": 0,
        "partial_count": 0,
        "missing_count": 0,
        "blockers": [],
        "blockers_met": 0,
        "blockers_remaining": 0,
        "optional_gaps": [],
        "high_risk_gaps": [],
        "suggested_delay": "Unknown",
        "rationale": "No deliverable data available for this gate.",
    }


def _build_rationale(decision, blockers_missing, blockers_partial, high_gaps, confidence, optional_gaps):
    parts = []
    if decision == "GO":
        parts.append("All required blockers are satisfied.")
        if optional_gaps:
            parts.append(f"{len(optional_gaps)} optional item(s) remain incomplete but do not block advancement.")
    elif decision == "NO-GO":
        if blockers_missing:
            names = [b.get("deliverable", "?") for b in blockers_missing]
            parts.append(f"Missing required blocker(s): {'; '.join(names)}.")
        if high_gaps:
            parts.append(f"{len(high_gaps)} high-risk gap(s) must be resolved.")
        if confidence < 50:
            parts.append(f"Evidence confidence is only {confidence}% — insufficient for advancement.")
    else:  # CONDITIONAL
        if blockers_partial:
            names = [b.get("deliverable", "?") for b in blockers_partial]
            parts.append(f"Partially complete blocker(s): {'; '.join(names)}.")
        if confidence < 70:
            parts.append(f"Confidence score ({confidence}%) is below the 70% threshold.")
        if optional_gaps:
            parts.append(f"{len(optional_gaps)} optional gap(s) should be addressed.")
    return " ".join(parts) if parts else "Assessment complete."


# ══════════════════════════════════════════════════════════════════════════════
# EXCEL EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def export_excel(analysis: dict, output_path: str):
    """
    Generate a multi-sheet Excel workbook from the analysis output.
    Sheets: Executive Summary, Checklist, Gap Analysis, Action Items
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()

    # Shared styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill_purple = PatternFill("solid", fgColor="5B35C4")
    header_fill_orange = PatternFill("solid", fgColor="FF6630")
    wrap = Alignment(wrap_text=True, vertical="top")
    thin_border = Border(
        left=Side(style="thin", color="D0D0D0"),
        right=Side(style="thin", color="D0D0D0"),
        top=Side(style="thin", color="D0D0D0"),
        bottom=Side(style="thin", color="D0D0D0"),
    )
    status_fills = {
        "PRESENT": PatternFill("solid", fgColor="E8F5E9"),
        "PARTIAL": PatternFill("solid", fgColor="FFF3E0"),
        "MISSING": PatternFill("solid", fgColor="FFEBEE"),
    }
    impact_fills = {
        "HIGH": PatternFill("solid", fgColor="FFEBEE"),
        "MEDIUM": PatternFill("solid", fgColor="FFF3E0"),
        "LOW": PatternFill("solid", fgColor="E8F5E9"),
    }

    def style_header(ws, cols, fill=None):
        for c, title in enumerate(cols, 1):
            cell = ws.cell(row=1, column=c, value=title)
            cell.font = header_font
            cell.fill = fill or header_fill_purple
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border

    def auto_width(ws, min_w=12, max_w=50):
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_len = max(max_len, min(len(str(cell.value)), max_w))
            ws.column_dimensions[col_letter].width = max(max_len + 2, min_w)

    # ── Sheet 1: Executive Summary ──
    ws1 = wb.active
    ws1.title = "Executive Summary"
    co = analysis.get("client_overview", {})
    m = analysis.get("metrics", {})
    ra = analysis.get("readiness_assessment", {})
    sg = m.get("stage_gate_completion", {})

    summary_data = [
        ("Client", co.get("client_name", "—")),
        ("Current Phase", co.get("current_phase", "—")),
        ("Overall Readiness", ra.get("overall_readiness", "—")),
        ("Next Gate Target", ra.get("next_gate", "—")),
        ("", ""),
        ("Coverage Score", f"{m.get('coverage_score', 0)}%"),
        ("Documents Analysed", m.get("total_documents", 0)),
        ("Documents Parsed", m.get("successfully_parsed", 0)),
        ("Total Gaps", m.get("total_gaps", 0)),
        ("High-Risk Gaps", m.get("high_risk_gaps", 0)),
        ("", ""),
        ("TG-1 Initiation", f"{sg.get('TG-1', 0)}%"),
        ("TG0 Design", f"{sg.get('TG0', 0)}%"),
        ("TG1 Implementation", f"{sg.get('TG1', 0)}%"),
        ("TG2 Test", f"{sg.get('TG2', 0)}%"),
        ("TG3 Deploy/Warranty", f"{sg.get('TG3', 0)}%"),
        ("", ""),
        ("Executive Summary", ra.get("executive_summary", "—")),
    ]

    # Append gate decisions to summary if available
    gd = analysis.get("gate_decisions", {})
    if gd:
        summary_data.append(("", ""))
        summary_data.append(("— GATE DECISIONS —", ""))
        for short, dec in gd.items():
            emoji = {"GO": "GO", "NO-GO": "NO-GO", "CONDITIONAL": "CONDITIONAL"}.get(dec.get("decision"), "?")
            summary_data.append((
                f"{dec.get('gate', short)}",
                f"{emoji} | Confidence: {dec.get('confidence_score', 0)}% | Risk: {dec.get('risk_severity', '?')} | Delay: {dec.get('suggested_delay', '?')}"
            ))

    style_header(ws1, ["Field", "Value"])
    for r, (field, val) in enumerate(summary_data, 2):
        ws1.cell(row=r, column=1, value=field).font = Font(bold=True) if field else Font()
        ws1.cell(row=r, column=2, value=str(val)).alignment = wrap
        for c in (1, 2):
            ws1.cell(row=r, column=c).border = thin_border
    ws1.column_dimensions["A"].width = 25
    ws1.column_dimensions["B"].width = 80

    # ── Sheet 2: Checklist ──
    ws2 = wb.create_sheet("Checklist")
    checklist_cols = [
        "Deliverable", "Stage Gate", "Owner", "Status", "Confidence",
        "Priority", "Est. Effort", "Evidence Files", "Notes"
    ]
    style_header(ws2, checklist_cols)
    for r, item in enumerate(analysis.get("checklist", []), 2):
        vals = [
            item.get("deliverable", ""),
            item.get("stage_gate", ""),
            item.get("responsibility", ""),
            item.get("status", ""),
            item.get("confidence", ""),
            item.get("priority", ""),
            item.get("estimated_effort", ""),
            ", ".join(item.get("evidence_files", [])),
            item.get("notes", ""),
        ]
        for c, v in enumerate(vals, 1):
            cell = ws2.cell(row=r, column=c, value=v)
            cell.alignment = wrap
            cell.border = thin_border
        # Color the status cell
        status_cell = ws2.cell(row=r, column=4)
        if status_cell.value in status_fills:
            status_cell.fill = status_fills[status_cell.value]
    auto_width(ws2)

    # ── Sheet 3: Gap Analysis ──
    ws3 = wb.create_sheet("Gap Analysis")
    gap_cols = [
        "Gap", "Impact", "Stage Gate", "Recommendation",
        "Responsible Party", "Est. Effort", "Dependencies"
    ]
    style_header(ws3, gap_cols, fill=header_fill_orange)
    for r, item in enumerate(analysis.get("gap_analysis", []), 2):
        vals = [
            item.get("gap", ""),
            item.get("impact", ""),
            item.get("stage_gate", ""),
            item.get("recommendation", ""),
            item.get("responsible_party", ""),
            item.get("estimated_effort", ""),
            ", ".join(item.get("dependencies", [])),
        ]
        for c, v in enumerate(vals, 1):
            cell = ws3.cell(row=r, column=c, value=v)
            cell.alignment = wrap
            cell.border = thin_border
        impact_cell = ws3.cell(row=r, column=2)
        if impact_cell.value in impact_fills:
            impact_cell.fill = impact_fills[impact_cell.value]
    auto_width(ws3)

    # ── Sheet 4: Action Items ──
    ws4 = wb.create_sheet("Action Items")
    action_cols = ["#", "Action", "Owner", "Priority", "Stage Gate", "Deliverable", "Est. Effort"]
    style_header(ws4, action_cols)
    for r, item in enumerate(analysis.get("action_items", []), 2):
        vals = [
            r - 1,
            item.get("action", ""),
            item.get("owner", ""),
            item.get("priority", ""),
            item.get("stage_gate", ""),
            item.get("deliverable", ""),
            item.get("estimated_effort", ""),
        ]
        for c, v in enumerate(vals, 1):
            cell = ws4.cell(row=r, column=c, value=v)
            cell.alignment = wrap
            cell.border = thin_border
    auto_width(ws4)

    # ── Sheet 5: Gate Decisions (Go / No-Go) ──
    gate_decisions = analysis.get("gate_decisions", {})
    if gate_decisions:
        ws_gd = wb.create_sheet("Gate Decisions")
        gd_cols = [
            "Stage Gate", "Decision", "Confidence", "Risk", "Completion",
            "Blockers Met", "Blockers Remaining", "Optional Gaps",
            "Suggested Delay", "Rationale"
        ]
        style_header(ws_gd, gd_cols, fill=PatternFill("solid", fgColor="1A0F3C"))
        decision_fills = {
            "GO": PatternFill("solid", fgColor="E8F5E9"),
            "CONDITIONAL": PatternFill("solid", fgColor="FFF3E0"),
            "NO-GO": PatternFill("solid", fgColor="FFEBEE"),
        }
        for r, (short, gd) in enumerate(gate_decisions.items(), 2):
            vals = [
                gd.get("gate", short),
                gd.get("decision", ""),
                f"{gd.get('confidence_score', 0)}%",
                gd.get("risk_severity", ""),
                f"{gd.get('completion_pct', 0)}%",
                str(gd.get("blockers_met", 0)),
                str(gd.get("blockers_remaining", 0)),
                str(len(gd.get("optional_gaps", []))),
                gd.get("suggested_delay", ""),
                gd.get("rationale", ""),
            ]
            for c, v in enumerate(vals, 1):
                cell = ws_gd.cell(row=r, column=c, value=v)
                cell.alignment = wrap
                cell.border = thin_border
            dec_cell = ws_gd.cell(row=r, column=2)
            if dec_cell.value in decision_fills:
                dec_cell.fill = decision_fills[dec_cell.value]
                dec_cell.font = Font(bold=True)
            risk_cell = ws_gd.cell(row=r, column=4)
            if risk_cell.value in impact_fills:
                risk_cell.fill = impact_fills[risk_cell.value]
        auto_width(ws_gd)

    # ── Sheet 6: Cross-Document Intelligence ──
    cross_intel = analysis.get("cross_document_intel")
    if cross_intel and cross_intel.get("cross_document_issues"):
        ws5 = wb.create_sheet("Cross-Doc Intelligence")
        cross_cols = [
            "#", "Category", "Severity", "Title", "Description",
            "Documents", "Evidence", "Recommendation", "Stage Gate", "Source"
        ]
        style_header(ws5, cross_cols, fill=PatternFill("solid", fgColor="1A0F3C"))
        severity_fills = {
            "HIGH": PatternFill("solid", fgColor="FFEBEE"),
            "MEDIUM": PatternFill("solid", fgColor="FFF3E0"),
            "LOW": PatternFill("solid", fgColor="E8F5E9"),
        }
        for r, issue in enumerate(cross_intel["cross_document_issues"], 2):
            vals = [
                r - 1,
                issue.get("category", ""),
                issue.get("severity", ""),
                issue.get("title", ""),
                issue.get("description", ""),
                ", ".join(issue.get("documents", [])),
                "\n".join(issue.get("evidence", [])),
                issue.get("recommendation", ""),
                issue.get("stage_gate", ""),
                issue.get("source", ""),
            ]
            for c, v in enumerate(vals, 1):
                cell = ws5.cell(row=r, column=c, value=v)
                cell.alignment = wrap
                cell.border = thin_border
            sev_cell = ws5.cell(row=r, column=3)
            if sev_cell.value in severity_fills:
                sev_cell.fill = severity_fills[sev_cell.value]
                sev_cell.font = Font(bold=True)
        auto_width(ws5)

        # Sheet 6: Cross-Reference Matrix
        matrix = cross_intel.get("cross_reference_matrix", [])
        if matrix:
            ws6 = wb.create_sheet("Cross-Reference Matrix")
            matrix_cols = ["Document A", "Document B", "Relationship", "Details"]
            style_header(ws6, matrix_cols, fill=PatternFill("solid", fgColor="1A0F3C"))
            for r, ref in enumerate(matrix, 2):
                vals = [
                    ref.get("document_a", ""),
                    ref.get("document_b", ""),
                    ref.get("relationship", ""),
                    ref.get("details", ""),
                ]
                for c, v in enumerate(vals, 1):
                    cell = ws6.cell(row=r, column=c, value=v)
                    cell.alignment = wrap
                    cell.border = thin_border
            auto_width(ws6)

    wb.save(output_path)
    print(f"  Excel report saved: {output_path}")
