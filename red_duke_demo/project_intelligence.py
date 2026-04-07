#!/usr/bin/env python3
"""
RED DUKE — Project Intelligence Engine ("The Brain")
=====================================================
Synthesizes ALL analysis data into a unified intelligence layer that:
  1. Computes multi-dimensional scores (Completeness, Quality, Consistency, Freshness)
  2. Derives Stage Readiness Scores from those dimensions
  3. Generates proactive recommendations ("Next 5 actions")
  4. Produces draft documents for missing deliverables (Gemini-powered)
  5. Creates a "Project Mind" narrative — the system's understanding of the project

This module is the final synthesis step in the pipeline. It consumes:
  - analysis_output (from analyzer.py)
  - cross_document_intel (from cross_document_intel.py)
  - parse_results (raw parsed documents)

Author: Sannidhya Tiwari
"""

import json
import os
import re
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# SDS STANDARD (imported for reference)
# ══════════════════════════════════════════════════════════════════════════════

SDS_STANDARD = {
    "TG-1 (Initiation)": [
        "Business Requirements Document (BRD)",
        "High-Level Project Plan / Critical Path",
        "Client Kickoff / Scope Presentation",
        "Security & Access Control Documentation",
        "Training & Process Awareness Documentation",
    ],
    "TG0 (Design)": [
        "Workflow / Process Flow Diagram",
        "Data Mapping Document",
        "Technical Design Specification",
        "BRD Sign-off",
    ],
    "TG1 (Implementation)": [
        "Implementation / Transition Workbook",
        "Configuration Documentation",
        "Reporting Requirements & SLA Documentation",
        "Mailroom / Workflow Configuration",
        "Eligibility & Claims Configuration",
    ],
    "TG2 (Test)": [
        "UAT Plan & Test Cases",
        "UAT Sign-off / Testing Evidence",
        "TPM / Compliance Checklist",
        "Functional & Volume Testing Evidence",
    ],
    "TG3 (Deploy/Warranty)": [
        "M2P / Go-Live Sign-off",
        "Post-Go-Live Warranty Checklist",
        "Lessons Learned Document",
        "Final Client Documentation Handoff",
    ],
}

# Gate ordering for progression logic
GATE_ORDER = ["TG-1", "TG0", "TG1", "TG2", "TG3"]
GATE_FULL = {
    "TG-1": "TG-1 (Initiation)",
    "TG0": "TG0 (Design)",
    "TG1": "TG1 (Implementation)",
    "TG2": "TG2 (Test)",
    "TG3": "TG3 (Deploy/Warranty)",
}


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-DIMENSIONAL SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _score_completeness(item: dict) -> int:
    """
    Completeness (0-100): How much of the deliverable exists?
    Based on status + evidence trail depth + evidence file count.
    """
    status = item.get("status", "MISSING")
    evidence_trail = item.get("evidence_trail", [])
    evidence_files = item.get("evidence_files", [])

    if status == "PRESENT":
        base = 75
        # Bonus for rich evidence
        trail_bonus = min(len(evidence_trail) * 8, 20)
        file_bonus = min(len(evidence_files) * 3, 5)
        return min(100, base + trail_bonus + file_bonus)
    elif status == "PARTIAL":
        base = 35
        trail_bonus = min(len(evidence_trail) * 10, 25)
        file_bonus = min(len(evidence_files) * 3, 5)
        return min(65, base + trail_bonus + file_bonus)
    else:
        return 0


def _score_quality(item: dict, doc_quality_map: dict) -> int:
    """
    Quality (0-100): AI-evaluated quality of the evidence.
    Derived from: confidence level + evidence file quality scores + evidence trail assessments.
    """
    status = item.get("status", "MISSING")
    if status == "MISSING":
        return 0

    confidence_map = {"HIGH": 80, "MEDIUM": 55, "LOW": 25}
    base = confidence_map.get(item.get("confidence", "LOW"), 25)

    # Factor in source document quality
    evidence_files = item.get("evidence_files", [])
    if evidence_files:
        file_qualities = []
        for f in evidence_files:
            q = doc_quality_map.get(f, "ADEQUATE")
            file_qualities.append({"STRONG": 90, "ADEQUATE": 60, "WEAK": 25}.get(q, 60))
        avg_file_quality = sum(file_qualities) / len(file_qualities)
        # Blend: 60% confidence-based, 40% file quality
        base = round(base * 0.6 + avg_file_quality * 0.4)

    # Bonus for having detailed evidence trail with assessments
    trail = item.get("evidence_trail", [])
    if trail:
        has_excerpts = sum(1 for t in trail if t.get("excerpt"))
        has_assessments = sum(1 for t in trail if t.get("assessment"))
        trail_bonus = min((has_excerpts + has_assessments) * 3, 15)
        base = min(100, base + trail_bonus)

    return base


def _score_consistency(item: dict, cross_intel: dict) -> int:
    """
    Consistency (0-100): Cross-document alignment for this deliverable.
    Based on whether any cross-doc issues reference the evidence files.
    """
    if item.get("status") == "MISSING":
        return 0

    evidence_files = set(item.get("evidence_files", []))
    if not evidence_files:
        return 50  # No files to cross-check, neutral score

    issues = cross_intel.get("cross_document_issues", [])
    relevant_issues = []
    for issue in issues:
        issue_docs = set(issue.get("documents", []))
        if issue_docs & evidence_files:
            relevant_issues.append(issue)

    if not relevant_issues:
        return 95  # No cross-doc issues found — high consistency

    # Deduct based on severity of relevant issues
    deductions = 0
    for issue in relevant_issues:
        sev = issue.get("severity", "LOW")
        deductions += {"HIGH": 25, "MEDIUM": 12, "LOW": 5}.get(sev, 5)

    return max(0, 95 - deductions)


def _score_freshness(item: dict, doc_metadata: dict) -> int:
    """
    Freshness (0-100): How current the evidence is.
    Based on dates found in evidence files and whether content appears to be final vs draft.
    """
    if item.get("status") == "MISSING":
        return 0

    evidence_files = item.get("evidence_files", [])
    if not evidence_files:
        return 50

    # Check evidence trail for draft/placeholder indicators
    trail = item.get("evidence_trail", [])
    draft_signals = 0
    for t in trail:
        excerpt = (t.get("excerpt", "") + " " + t.get("assessment", "")).lower()
        for signal in ["tbd", "placeholder", "draft", "pending", "todo", "to be determined",
                       "needs update", "work in progress", "wip", "incomplete"]:
            if signal in excerpt:
                draft_signals += 1
                break

    if draft_signals > 0:
        # Penalize for draft content
        return max(10, 60 - draft_signals * 15)

    # Check document metadata for recency
    freshness_scores = []
    for f in evidence_files:
        meta = doc_metadata.get(f, {})
        # If the doc has many sections and tables, it's likely more complete
        sections = meta.get("sections", 0)
        tables = meta.get("tables", 0)
        if sections > 3 or tables > 1:
            freshness_scores.append(85)
        elif sections > 0:
            freshness_scores.append(70)
        else:
            freshness_scores.append(55)

    return round(sum(freshness_scores) / len(freshness_scores)) if freshness_scores else 65


def compute_deliverable_scores(analysis: dict, cross_intel: dict, parse_results: list) -> list:
    """
    Compute multi-dimensional scores for every checklist item.
    Returns enriched checklist with scores attached.
    """
    # Build document quality map from analysis
    doc_quality_map = {}
    for doc in analysis.get("documents", []):
        doc_quality_map[doc.get("filename", "")] = doc.get("quality_score", "ADEQUATE")

    # Build document metadata map from parse results
    doc_metadata = {}
    for r in parse_results:
        doc_metadata[r.filename] = {
            "sections": len(r.sections),
            "tables": len(r.tables),
            "word_count": r.word_count,
            "file_size": r.file_size,
        }

    scored_checklist = []
    for item in analysis.get("checklist", []):
        completeness = _score_completeness(item)
        quality = _score_quality(item, doc_quality_map)
        consistency = _score_consistency(item, cross_intel or {})
        freshness = _score_freshness(item, doc_metadata)

        # Stage Readiness Score: weighted composite
        # Completeness: 40%, Quality: 25%, Consistency: 20%, Freshness: 15%
        readiness = round(
            completeness * 0.40 +
            quality * 0.25 +
            consistency * 0.20 +
            freshness * 0.15
        )

        scored_item = {
            **item,
            "scores": {
                "completeness": completeness,
                "quality": quality,
                "consistency": consistency,
                "freshness": freshness,
                "readiness": readiness,
            },
        }
        scored_checklist.append(scored_item)

    return scored_checklist


# ══════════════════════════════════════════════════════════════════════════════
# STAGE READINESS SCORES
# ══════════════════════════════════════════════════════════════════════════════

def compute_stage_readiness(scored_checklist: list) -> dict:
    """
    Compute a multi-dimensional readiness score for each stage gate.
    """
    stage_scores = {}

    for gate_short, gate_full in GATE_FULL.items():
        gate_items = [
            c for c in scored_checklist
            if c.get("stage_gate") == gate_full
        ]

        if not gate_items:
            stage_scores[gate_short] = {
                "gate": gate_full,
                "completeness": 0,
                "quality": 0,
                "consistency": 0,
                "freshness": 0,
                "readiness": 0,
                "item_count": 0,
            }
            continue

        dims = ["completeness", "quality", "consistency", "freshness", "readiness"]
        averages = {}
        for dim in dims:
            values = [c["scores"][dim] for c in gate_items if c.get("scores")]
            averages[dim] = round(sum(values) / len(values)) if values else 0

        stage_scores[gate_short] = {
            "gate": gate_full,
            **averages,
            "item_count": len(gate_items),
        }

    return stage_scores


# ══════════════════════════════════════════════════════════════════════════════
# PROACTIVE RECOMMENDATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def generate_proactive_actions(analysis: dict, scored_checklist: list, cross_intel: dict) -> list:
    """
    Generate the top prioritized next actions.
    Uses a scoring algorithm to rank actions by impact.
    """
    candidates = []

    # Source 1: Missing/Partial deliverables (from scored checklist)
    for item in scored_checklist:
        if item.get("status") == "MISSING":
            impact = 100 if item.get("is_blocker") else 60
            if item.get("priority") == "P1":
                impact += 30
            elif item.get("priority") == "P2":
                impact += 15

            effort_map = {"Small (< 1 day)": 3, "Medium (1-3 days)": 2, "Large (3+ days)": 1}
            effort_bonus = effort_map.get(item.get("estimated_effort", ""), 1)
            impact += effort_bonus * 5

            candidates.append({
                "action": f"Create {item['deliverable']}",
                "type": "create_deliverable",
                "deliverable": item.get("deliverable", ""),
                "stage_gate": item.get("stage_gate", ""),
                "owner": item.get("responsibility", ""),
                "impact_score": impact,
                "effort": item.get("estimated_effort", "Medium (1-3 days)"),
                "reason": f"This deliverable is MISSING and {'blocks the stage gate' if item.get('is_blocker') else 'is needed for complete coverage'}.",
                "can_generate_draft": True,
            })
        elif item.get("status") == "PARTIAL":
            readiness = item.get("scores", {}).get("readiness", 0)
            impact = 80 if item.get("is_blocker") else 50
            gap_to_close = 100 - readiness
            impact += round(gap_to_close * 0.3)

            candidates.append({
                "action": f"Complete {item['deliverable']}",
                "type": "complete_deliverable",
                "deliverable": item.get("deliverable", ""),
                "stage_gate": item.get("stage_gate", ""),
                "owner": item.get("responsibility", ""),
                "impact_score": impact,
                "effort": item.get("estimated_effort", "Small (< 1 day)"),
                "reason": f"Readiness score is {readiness}%. {item.get('notes', '')}",
                "can_generate_draft": True,
            })

    # Source 2: Cross-doc issues (from cross_intel)
    if cross_intel:
        for issue in cross_intel.get("cross_document_issues", [])[:5]:
            sev_impact = {"HIGH": 85, "MEDIUM": 55, "LOW": 30}.get(issue.get("severity", "LOW"), 30)
            candidates.append({
                "action": f"Resolve: {issue.get('title', 'Cross-document inconsistency')}",
                "type": "resolve_inconsistency",
                "deliverable": ", ".join(issue.get("documents", [])),
                "stage_gate": issue.get("stage_gate", ""),
                "owner": "Engineering",
                "impact_score": sev_impact,
                "effort": "Small (< 1 day)",
                "reason": issue.get("description", "")[:200],
                "can_generate_draft": False,
            })

    # Sort by impact score descending
    candidates.sort(key=lambda x: x["impact_score"], reverse=True)

    # Return top actions with rank
    top_actions = []
    for i, c in enumerate(candidates[:10]):
        c["rank"] = i + 1
        top_actions.append(c)

    return top_actions


# ══════════════════════════════════════════════════════════════════════════════
# GATE DECISIONS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def generate_gate_decisions(scored_checklist: list, stage_readiness: dict, gap_analysis: list) -> dict:
    """
    Generate Go / Conditional / No-Go decisions for each stage gate.
    Returns a dict keyed by gate short name (TG-1, TG0, etc.).
    """
    gate_decisions = {}

    for gate_short, gate_full in GATE_FULL.items():
        readiness = stage_readiness.get(gate_short, {})
        readiness_score = readiness.get("readiness", 0)
        item_count = readiness.get("item_count", 0)

        # Get checklist items for this gate
        gate_items = [
            c for c in scored_checklist
            if c.get("stage_gate") == gate_full
        ]

        # Identify blockers (items that are critical for gate passage)
        blockers = []
        for item in gate_items:
            status = item.get("status", "MISSING")
            blockers.append({
                "deliverable": item.get("deliverable", ""),
                "status": status,
                "owner": item.get("responsibility", ""),
                "effort": item.get("estimated_effort", "Medium (1-3 days)"),
                "notes": item.get("notes", ""),
            })

        blockers_met = sum(1 for b in blockers if b["status"] == "PRESENT")
        blockers_remaining = len(blockers) - blockers_met

        # Get gaps for this gate
        gate_gaps = [
            g for g in gap_analysis
            if g.get("stage_gate", "") == gate_full
        ]
        high_risk_gaps = [g.get("gap", "") for g in gate_gaps if g.get("impact") == "HIGH"]
        optional_gaps = [
            {
                "deliverable": g.get("gap", ""),
                "status": "MISSING",
                "effort": "Medium (1-3 days)",
            }
            for g in gate_gaps if g.get("impact") != "HIGH"
        ]

        # Compute completion percentage
        if len(gate_items) > 0:
            present = sum(1 for c in gate_items if c.get("status") == "PRESENT")
            partial = sum(1 for c in gate_items if c.get("status") == "PARTIAL")
            completion_pct = round(((present + partial * 0.5) / len(gate_items)) * 100)
        else:
            completion_pct = 0

        # Decision logic
        if readiness_score >= 70 and blockers_remaining == 0 and len(high_risk_gaps) == 0:
            decision = "GO"
            confidence = min(95, readiness_score + 10)
            rationale = (
                f"All {item_count} deliverables are accounted for with a readiness score of "
                f"{readiness_score}%. No critical blockers or high-risk gaps remain."
            )
            suggested_delay = "None"
        elif readiness_score >= 40 or (blockers_met > 0 and blockers_remaining <= 2):
            decision = "CONDITIONAL"
            confidence = max(30, readiness_score)
            missing_list = [b["deliverable"] for b in blockers if b["status"] != "PRESENT"]
            rationale = (
                f"Partial readiness at {readiness_score}%. "
                f"{blockers_remaining} blocker(s) remain: {', '.join(missing_list[:3])}. "
                f"Gate passage is possible once these items are addressed."
            )
            suggested_delay = "1-2 weeks" if blockers_remaining <= 2 else "2-4 weeks"
        else:
            decision = "NO-GO"
            confidence = max(20, 100 - readiness_score)
            missing_list = [b["deliverable"] for b in blockers if b["status"] == "MISSING"]
            rationale = (
                f"Readiness score is {readiness_score}% — well below the threshold. "
                f"{len(missing_list)} deliverable(s) are MISSING: {', '.join(missing_list[:3])}. "
                f"Significant work is needed before this gate can be considered."
            )
            suggested_delay = "1-2 months" if len(missing_list) > 3 else "3-6 weeks"

        # Confidence score (0-100)
        confidence_score = min(100, max(10, confidence))

        gate_decisions[gate_short] = {
            "decision": decision,
            "confidence_score": confidence_score,
            "rationale": rationale,
            "completion_pct": completion_pct,
            "blockers": blockers,
            "blockers_met": blockers_met,
            "blockers_remaining": blockers_remaining,
            "optional_gaps": optional_gaps[:5],
            "high_risk_gaps": high_risk_gaps[:5],
            "suggested_delay": suggested_delay,
        }

    return gate_decisions


# ══════════════════════════════════════════════════════════════════════════════
# DRAFT DOCUMENT GENERATOR (Gemini-powered)
# ══════════════════════════════════════════════════════════════════════════════

GEMINI_MODEL = "gemini-2.5-flash-lite"


def generate_draft_document(deliverable_name: str, stage_gate: str, analysis: dict, parse_results: list) -> dict:
    """
    Generate a context-aware draft document for a missing deliverable.
    Uses information from ALL parsed documents to pre-fill the draft.
    """
    from analyzer import get_client, _ensure_genai
    _ensure_genai()
    from google.genai import types

    # Gather context from all documents
    context_snippets = []
    for r in parse_results:
        if not r.success:
            continue
        snippet = r.text[:3000]
        context_snippets.append(f"[{r.filename}]: {snippet}")

    context_text = "\n\n".join(context_snippets[:8])  # Limit to 8 docs for prompt size

    client_overview = analysis.get("client_overview", {})
    client_name = client_overview.get("client_name", "Client")
    scope = client_overview.get("scope", "")
    integrations = ", ".join(client_overview.get("integrations", [])[:10])

    prompt = f"""You are RED DUKE, generating a DRAFT document for a healthcare implementation project at Smart Data Solutions (SDS).

CLIENT: {client_name}
SCOPE: {scope}
INTEGRATIONS: {integrations}
STAGE GATE: {stage_gate}
DELIVERABLE NEEDED: {deliverable_name}

You have context from the existing project documents:
{context_text}

Generate a professional, detailed DRAFT of "{deliverable_name}" that:
1. Is pre-filled with real data extracted from the existing documents above
2. Uses proper section structure with headings
3. Includes [ACTION REQUIRED] markers where human input is still needed
4. References specific systems, integrations, and data points from the project
5. Follows healthcare/SDS industry standards
6. Is ready for a PM or Engineer to review and finalize

Return ONLY a JSON object with this structure:
{{
  "title": "{deliverable_name}",
  "stage_gate": "{stage_gate}",
  "generated_at": "{datetime.now().isoformat()}",
  "status": "DRAFT — Requires Review",
  "sections": [
    {{
      "heading": "section title",
      "content": "detailed section content with real data from the project. Use [ACTION REQUIRED: description] markers where human input is needed.",
      "completion_pct": 0
    }}
  ],
  "action_required_count": 0,
  "estimated_completion_effort": "Small/Medium/Large",
  "notes": "brief note about what data was used to pre-fill this draft and what still needs human review"
}}

CRITICAL: Use REAL data from the documents — names, systems, field names, dates, SLA numbers. Do NOT use generic placeholders like 'Company X'. Mark only genuinely unknown items with [ACTION REQUIRED]."""

    client = get_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    draft = json.loads(raw)

    # Count action required markers
    total_actions = 0
    for section in draft.get("sections", []):
        content = section.get("content", "")
        total_actions += len(re.findall(r'\[ACTION REQUIRED[^\]]*\]', content))
    draft["action_required_count"] = total_actions

    return draft


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT MIND — UNIFIED SYNTHESIS
# ══════════════════════════════════════════════════════════════════════════════

def generate_project_mind(analysis: dict, cross_intel: dict, parse_results: list) -> dict:
    """
    Generate a unified "Project Mind" synthesis from Gemini.
    This is the system's coherent understanding of the entire project.
    """
    from analyzer import get_client, _ensure_genai
    _ensure_genai()
    from google.genai import types

    # Summarize all intelligence for the prompt
    co = analysis.get("client_overview", {})
    checklist = analysis.get("checklist", [])
    gaps = analysis.get("gap_analysis", [])
    gate_decisions = analysis.get("gate_decisions", {})

    present = sum(1 for c in checklist if c.get("status") == "PRESENT")
    partial = sum(1 for c in checklist if c.get("status") == "PARTIAL")
    missing = sum(1 for c in checklist if c.get("status") == "MISSING")
    high_gaps = sum(1 for g in gaps if g.get("impact") == "HIGH")

    cross_issues = 0
    consistency = 100
    if cross_intel:
        cross_issues = cross_intel.get("total_issues", 0)
        consistency = cross_intel.get("consistency_score", 100)

    # Gate decision summary
    gate_summary = []
    for short in GATE_ORDER:
        gd = gate_decisions.get(short, {})
        gate_summary.append(f"{short}: {gd.get('decision', '?')} (confidence: {gd.get('confidence_score', 0)}%)")

    doc_names = [r.filename for r in parse_results if r.success]

    prompt = f"""You are RED DUKE — the intelligent brain of an SDS healthcare implementation analysis system. You have deeply analyzed a client project and now must synthesize your understanding into a cohesive intelligence briefing.

PROJECT CONTEXT:
Client: {co.get('client_name', '?')}
Phase: {co.get('current_phase', '?')}
Scope: {co.get('scope', '?')}
Documents analyzed: {', '.join(doc_names)}

ANALYSIS RESULTS:
- Deliverables: {present} present, {partial} partial, {missing} missing (of {len(checklist)} total)
- Gaps: {high_gaps} high-risk, {len(gaps)} total
- Cross-document issues: {cross_issues} (consistency score: {consistency}%)
- Gate decisions: {'; '.join(gate_summary)}

Return ONLY a JSON object:
{{
  "project_understanding": "3-4 paragraphs. Write as if you are the system's brain explaining what you understand about this project. Be specific — name documents, cite numbers, reference decisions. Explain where the project IS, not just where it should be. Show that you understand the relationships between documents and what they collectively reveal.",
  "critical_insight": "One sentence — the single most important thing leadership needs to know right now. Make it specific and actionable.",
  "risk_narrative": "2-3 sentences explaining the biggest risk to this project and why it matters. Be specific — don't say 'documentation gaps', say exactly which gap and what it blocks.",
  "momentum_assessment": "ACCELERATING if the project has strong forward momentum, STEADY if progressing normally, STALLING if losing momentum, BLOCKED if cannot advance",
  "momentum_reason": "1-2 sentences explaining the momentum assessment",
  "predicted_bottleneck": "The specific deliverable, sign-off, or dependency most likely to delay the project next. Name it exactly.",
  "time_to_next_gate": "Estimated calendar time to reach the next gate (e.g. '2-3 weeks', '1 month')",
  "next_actions_narrative": "2-3 sentences: if you were the PM, what would you do TOMORROW MORNING? Be very specific — name the meeting, the document, the person."
}}"""

    client = get_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.15,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return json.loads(raw)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def run_project_intelligence(analysis: dict, cross_intel: dict, parse_results: list) -> dict:
    """
    Full Project Intelligence pipeline.
    Returns the unified intelligence dict.
    """
    print("\n  Phase 1: Computing multi-dimensional scores...")
    scored_checklist = compute_deliverable_scores(analysis, cross_intel, parse_results)

    print("  Phase 2: Computing stage readiness scores...")
    stage_readiness = compute_stage_readiness(scored_checklist)
    for gate, scores in stage_readiness.items():
        print(f"    {gate}: readiness={scores['readiness']}% "
              f"(C:{scores['completeness']} Q:{scores['quality']} "
              f"X:{scores['consistency']} F:{scores['freshness']})")

    print("  Phase 3: Generating gate decisions...")
    gap_analysis = analysis.get("gap_analysis", [])
    gate_decisions = generate_gate_decisions(scored_checklist, stage_readiness, gap_analysis)
    for gate, gd in gate_decisions.items():
        print(f"    {gate}: {gd['decision']} (confidence: {gd['confidence_score']}%)")

    print("  Phase 4: Generating proactive recommendations...")
    proactive_actions = generate_proactive_actions(analysis, scored_checklist, cross_intel)
    print(f"    Generated {len(proactive_actions)} prioritized actions")

    print("  Phase 5: Generating Project Mind synthesis (Gemini)...")
    # Inject gate_decisions into analysis so the Project Mind prompt can use them
    analysis["gate_decisions"] = gate_decisions
    project_mind = generate_project_mind(analysis, cross_intel, parse_results)

    # Compute overall project readiness (weighted average of all gates)
    gate_readiness_values = [s["readiness"] for s in stage_readiness.values() if s["item_count"] > 0]
    overall_readiness = round(sum(gate_readiness_values) / len(gate_readiness_values)) if gate_readiness_values else 0

    result = {
        "scored_checklist": scored_checklist,
        "stage_readiness": stage_readiness,
        "gate_decisions": gate_decisions,
        "proactive_actions": proactive_actions,
        "project_mind": project_mind,
        "overall_readiness_score": overall_readiness,
        "generated_at": datetime.now().isoformat(),
    }

    print(f"\n  Project Intelligence Complete:")
    print(f"    Overall readiness:  {overall_readiness}%")
    print(f"    Momentum:           {project_mind.get('momentum_assessment', '?')}")
    print(f"    Critical insight:   {project_mind.get('critical_insight', '?')[:100]}...")

    return result
