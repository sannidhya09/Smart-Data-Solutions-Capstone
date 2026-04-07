#!/usr/bin/env python3
"""
RED DUKE — Cross-Document Intelligence Engine
==============================================
Detects inconsistencies, contradictions, and mismatches across
all parsed documents in a client implementation folder.

Categories of cross-document issues:
  1. Field/Schema Mismatches   — e.g. member_id vs memberID vs MemberId
  2. Timeline Conflicts        — contradictory dates, milestones, deadlines
  3. Terminology Drift         — same concept referred to by different names
  4. Requirements ↔ Impl Gaps  — something required in one doc but absent/different in another
  5. Numeric/Metric Conflicts  — SLA, volume, or threshold numbers that don't agree

Uses a two-phase approach:
  Phase 1: Local extraction — regex/NLP pulls structured entities from each doc
  Phase 2: Gemini analysis  — AI cross-references all extractions for deep conflicts

Author: Sannidhya Tiwari
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExtractedEntity:
    """A structured entity pulled from a single document."""
    entity_type: str          # field_name | date | term | metric | reference
    value: str                # the raw value found
    normalized: str           # lowercased/cleaned for comparison
    source_file: str
    context: str              # surrounding text snippet
    section: str = ""         # section title where found


@dataclass
class CrossDocIssue:
    """A detected inconsistency between two or more documents."""
    category: str             # field_mismatch | timeline_conflict | terminology_drift |
                              # requirement_gap | metric_conflict
    severity: str             # HIGH | MEDIUM | LOW
    title: str                # short human-readable title
    description: str          # detailed explanation
    documents: list = field(default_factory=list)      # filenames involved
    evidence: list = field(default_factory=list)        # specific values/snippets from each doc
    recommendation: str = ""
    stage_gate: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1: LOCAL ENTITY EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

# Patterns for field/column names (snake_case, camelCase, PascalCase, UPPER_CASE)
_FIELD_PATTERN = re.compile(
    r'\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b'          # snake_case
    r'|'
    r'\b([a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)+)\b'       # camelCase
    r'|'
    r'\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b'       # PascalCase
    r'|'
    r'\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b',          # UPPER_CASE
    re.MULTILINE,
)

# Date patterns (ISO, US, written)
_DATE_PATTERN = re.compile(
    r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'                          # 2025-03-15
    r'|'
    r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'                        # 03/15/2025
    r'|'
    r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    r'(?:uary|ruary|ch|il|e|ust|tember|ober|ember)?'
    r'\s+\d{1,2},?\s*\d{4})\b',                                   # March 15, 2025
    re.IGNORECASE,
)

# Metric/SLA patterns (numbers with units or percentages)
_METRIC_PATTERN = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*(%|percent|days?|hours?|minutes?|ms|seconds?|SLA|business days?)\b',
    re.IGNORECASE,
)

# Common healthcare/SDS field synonyms for normalization
_SYNONYM_GROUPS = [
    {"member_id", "memberid", "member id", "mbr_id", "mbrid"},
    {"provider_id", "providerid", "provider id", "prov_id", "provid", "npi"},
    {"claim_id", "claimid", "claim id", "clm_id", "clmid"},
    {"date_of_service", "dateofservice", "dos", "service_date", "servicedate", "svc_date"},
    {"date_of_birth", "dateofbirth", "dob", "birth_date", "birthdate"},
    {"group_id", "groupid", "group id", "grp_id", "grpid"},
    {"subscriber_id", "subscriberid", "subscriber id", "sub_id", "subid"},
    {"tax_id", "taxid", "tax id", "tin", "federal_tax_id"},
    {"go_live", "golive", "go live", "go-live", "move_to_production", "m2p"},
    {"uat", "user_acceptance_testing", "user acceptance testing", "acceptance_test"},
]

# Build a lookup: normalized term → group label
_SYNONYM_LOOKUP = {}
for group in _SYNONYM_GROUPS:
    label = sorted(group, key=len)[-1]  # longest form as canonical
    for term in group:
        _SYNONYM_LOOKUP[term.lower().replace(" ", "").replace("_", "").replace("-", "")] = label


def _normalize_field(value: str) -> str:
    """Normalize a field name for comparison: lowercase, strip separators."""
    return re.sub(r'[_\-\s]', '', value.lower())


def _get_context(text: str, match_start: int, match_end: int, window: int = 80) -> str:
    """Extract surrounding context for a match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    ctx = text[start:end].replace('\n', ' ').strip()
    if start > 0:
        ctx = '...' + ctx
    if end < len(text):
        ctx = ctx + '...'
    return ctx


def extract_entities(parse_result) -> list[ExtractedEntity]:
    """Extract structured entities from a single parsed document."""
    entities = []
    text = parse_result.text or ""
    filename = parse_result.filename

    if not text.strip():
        return entities

    # Determine current section for each position
    section_map = []
    if parse_result.sections:
        for sec in parse_result.sections:
            section_map.append(sec.get("title", ""))

    current_section = section_map[0] if section_map else ""

    # ── Field names ──
    seen_fields = set()
    for match in _FIELD_PATTERN.finditer(text):
        raw = match.group(0)
        if raw is None:
            continue
        norm = _normalize_field(raw)
        if len(norm) < 4 or len(norm) > 40:
            continue
        if norm in seen_fields:
            continue
        seen_fields.add(norm)

        # Check if it maps to a known synonym
        canonical = _SYNONYM_LOOKUP.get(norm, norm)

        entities.append(ExtractedEntity(
            entity_type="field_name",
            value=raw,
            normalized=canonical,
            source_file=filename,
            context=_get_context(text, match.start(), match.end()),
        ))

    # ── Dates ──
    seen_dates = set()
    for match in _DATE_PATTERN.finditer(text):
        raw = match.group(0)
        if raw is None:
            continue
        if raw in seen_dates:
            continue
        seen_dates.add(raw)

        entities.append(ExtractedEntity(
            entity_type="date",
            value=raw,
            normalized=raw.lower().strip(),
            source_file=filename,
            context=_get_context(text, match.start(), match.end()),
        ))

    # ── Metrics/SLAs ──
    seen_metrics = set()
    for match in _METRIC_PATTERN.finditer(text):
        number = match.group(1)
        unit = match.group(2)
        raw = f"{number} {unit}"
        if raw in seen_metrics:
            continue
        seen_metrics.add(raw)

        entities.append(ExtractedEntity(
            entity_type="metric",
            value=raw,
            normalized=f"{number} {unit.lower()}",
            source_file=filename,
            context=_get_context(text, match.start(), match.end()),
        ))

    return entities


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1.5: LOCAL CONFLICT DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_local_conflicts(all_entities: dict[str, list[ExtractedEntity]]) -> list[CrossDocIssue]:
    """
    Find obvious conflicts by comparing extracted entities across documents.
    This runs without AI — pure pattern matching.
    """
    issues = []

    # ── Field name mismatches ──
    # Group by normalized canonical form, flag when different raw forms appear across docs
    field_groups = defaultdict(list)
    for filename, entities in all_entities.items():
        for e in entities:
            if e.entity_type == "field_name":
                field_groups[e.normalized].append(e)

    for canonical, group in field_groups.items():
        # Get unique (raw_value, source_file) pairs
        variants = {}
        for e in group:
            if e.value not in variants:
                variants[e.value] = e

        if len(variants) < 2:
            continue

        # Check if variants come from different files
        files = set(e.source_file for e in variants.values())
        if len(files) < 2:
            continue

        evidence = []
        docs = []
        for raw, e in variants.items():
            evidence.append(f'"{raw}" in {e.source_file}: {e.context[:100]}')
            docs.append(e.source_file)

        issues.append(CrossDocIssue(
            category="field_mismatch",
            severity="HIGH",
            title=f"Field naming inconsistency: {', '.join(variants.keys())}",
            description=(
                f"The same data concept '{canonical}' is referred to by different names "
                f"across documents: {', '.join(variants.keys())}. "
                f"This can cause mapping errors, failed data integrations, and silent data loss."
            ),
            documents=list(set(docs)),
            evidence=evidence,
            recommendation=(
                f"Standardize on a single field name (recommend: {canonical}) "
                f"and update all documents and configurations to match."
            ),
        ))

    # ── Metric conflicts ──
    # Group metrics by their unit and surrounding context keywords
    metric_by_context = defaultdict(list)
    for filename, entities in all_entities.items():
        for e in entities:
            if e.entity_type == "metric":
                # Extract context keywords to group related metrics
                ctx_lower = e.context.lower()
                for keyword in ["sla", "turnaround", "response", "volume", "threshold",
                                "accuracy", "uptime", "availability", "latency"]:
                    if keyword in ctx_lower:
                        metric_by_context[(keyword, e.normalized.split()[-1])].append(e)
                        break

    for (keyword, unit), group in metric_by_context.items():
        values = {}
        for e in group:
            number = e.value.split()[0]
            if number not in values:
                values[number] = e

        if len(values) < 2:
            continue

        files = set(e.source_file for e in values.values())
        if len(files) < 2:
            continue

        evidence = [f'{e.value} in {e.source_file}: {e.context[:100]}' for e in values.values()]
        issues.append(CrossDocIssue(
            category="metric_conflict",
            severity="HIGH" if keyword == "sla" else "MEDIUM",
            title=f"Conflicting {keyword} values: {', '.join(values.keys())} {unit}",
            description=(
                f"Different documents specify different {keyword} values: "
                f"{', '.join(f'{v.value} ({v.source_file})' for v in values.values())}. "
                f"Misaligned metrics can lead to SLA breaches and incorrect client expectations."
            ),
            documents=list(files),
            evidence=evidence,
            recommendation=(
                f"Reconcile the {keyword} values across all documents. "
                f"Confirm the authoritative value with the client and update all references."
            ),
        ))

    return issues


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: GEMINI DEEP CROSS-REFERENCE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_CHARS_PER_DOC = 8000


def _build_cross_intel_prompt(
    parse_results: list,
    local_entities: dict[str, list[ExtractedEntity]],
    local_issues: list[CrossDocIssue],
) -> str:
    """Build the Gemini prompt for deep cross-document analysis."""

    # Summarize documents
    doc_summaries = []
    for r in parse_results:
        if not r.success:
            continue
        snippet = r.text[:MAX_CHARS_PER_DOC]
        doc_summaries.append(
            f"=== DOCUMENT: {r.filename} ===\n"
            f"Type: {r.file_type}\n"
            f"Content:\n{snippet}\n"
        )
    documents_text = "\n".join(doc_summaries)

    # Summarize local findings
    local_entity_summary = []
    for filename, entities in local_entities.items():
        fields = [e.value for e in entities if e.entity_type == "field_name"]
        dates = [e.value for e in entities if e.entity_type == "date"]
        metrics = [e.value for e in entities if e.entity_type == "metric"]
        if fields or dates or metrics:
            local_entity_summary.append(
                f"{filename}:\n"
                f"  Fields: {', '.join(fields[:20]) if fields else 'none'}\n"
                f"  Dates: {', '.join(dates[:10]) if dates else 'none'}\n"
                f"  Metrics: {', '.join(metrics[:10]) if metrics else 'none'}\n"
            )

    entities_text = "\n".join(local_entity_summary) if local_entity_summary else "No entities extracted."

    local_issues_text = ""
    if local_issues:
        items = []
        for issue in local_issues:
            items.append(f"- [{issue.category}] {issue.title}: {issue.description[:150]}")
        local_issues_text = "\n".join(items)
    else:
        local_issues_text = "No local conflicts detected."

    n_docs = len([r for r in parse_results if r.success])

    return f"""You are RED DUKE's Cross-Document Intelligence Engine. You specialize in finding inconsistencies, contradictions, and mismatches BETWEEN documents in a client implementation folder.

You have {n_docs} documents from a healthcare implementation project at Smart Data Solutions (SDS).

YOUR MISSION: Find cross-document issues that humans typically miss. Focus on:
1. FIELD/SCHEMA MISMATCHES — Same data field called different names across docs (e.g., member_id vs memberID vs MemberId)
2. TIMELINE CONFLICTS — Dates, deadlines, milestones that contradict each other across docs
3. TERMINOLOGY DRIFT — Same concept referred to by different names or acronyms
4. REQUIREMENTS ↔ IMPLEMENTATION GAPS — Something specified in one doc but missing, different, or contradicted in another
5. NUMERIC/METRIC CONFLICTS — SLAs, volumes, thresholds, or counts that don't agree across docs

EXTRACTED ENTITIES (from local analysis):
{entities_text}

LOCAL CONFLICTS ALREADY DETECTED:
{local_issues_text}

CLIENT DOCUMENTS:
{documents_text}

Return ONLY a single valid JSON object (no markdown fences, no extra text) with EXACTLY this structure:

{{
  "cross_document_issues": [
    {{
      "category": "field_mismatch | timeline_conflict | terminology_drift | requirement_gap | metric_conflict",
      "severity": "HIGH | MEDIUM | LOW",
      "title": "Short descriptive title of the inconsistency",
      "description": "Detailed explanation: what exactly conflicts, where, and why it matters. Be specific — quote actual values from the documents.",
      "documents": ["file1.docx", "file2.xlsx"],
      "evidence": [
        "In file1.docx: 'member_id is used in the API spec on page 3'",
        "In file2.xlsx: 'memberID column in the mapping sheet'"
      ],
      "recommendation": "Concrete action to resolve this inconsistency",
      "stage_gate": "Which SDS stage gate this affects (TG-1, TG0, TG1, TG2, TG3)"
    }}
  ],
  "cross_reference_matrix": [
    {{
      "document_a": "filename",
      "document_b": "filename",
      "relationship": "supports | contradicts | extends | depends_on | duplicates",
      "details": "How these two documents relate and any issues between them"
    }}
  ],
  "consistency_score": 0,
  "summary": "2-3 sentences: overall cross-document consistency assessment. What is the biggest risk?",
  "total_issues": 0,
  "high_severity_count": 0,
  "medium_severity_count": 0,
  "low_severity_count": 0
}}

CRITICAL INSTRUCTIONS:
- Do NOT repeat the local conflicts already detected — find NEW issues
- Be specific: quote actual values, field names, dates from the documents
- Focus on issues that have real business impact in healthcare implementations
- consistency_score is 0-100 (100 = perfectly consistent, 0 = major contradictions)
- total_issues, high/medium/low counts must be accurate integers
- Include at least the cross_reference_matrix for every pair of related documents
- Return ONLY the JSON object. No markdown. No explanation."""


def run_cross_document_analysis(parse_results: list) -> dict:
    """
    Full cross-document intelligence pipeline.
    Returns the combined analysis dict ready for JSON serialization.
    """
    print("\n  Phase 1: Extracting entities from each document...")
    all_entities = {}
    for r in parse_results:
        if not r.success:
            continue
        entities = extract_entities(r)
        all_entities[r.filename] = entities
        field_count = sum(1 for e in entities if e.entity_type == "field_name")
        date_count = sum(1 for e in entities if e.entity_type == "date")
        metric_count = sum(1 for e in entities if e.entity_type == "metric")
        print(f"    {r.filename}: {field_count} fields, {date_count} dates, {metric_count} metrics")

    print("\n  Phase 1.5: Detecting local conflicts...")
    local_issues = detect_local_conflicts(all_entities)
    print(f"    Found {len(local_issues)} local conflict(s)")

    print("\n  Phase 2: Running Gemini deep cross-reference analysis...")
    # Import Gemini client from analyzer module
    from analyzer import get_client, _ensure_genai
    _ensure_genai()
    from google.genai import types

    client = get_client()
    prompt = _build_cross_intel_prompt(parse_results, all_entities, local_issues)
    print(f"    Prompt size: {len(prompt):,} characters")

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    gemini_result = json.loads(raw)

    # ── Merge local + Gemini issues ──
    combined_issues = []

    # Add local issues first
    for issue in local_issues:
        combined_issues.append({
            "category": issue.category,
            "severity": issue.severity,
            "title": issue.title,
            "description": issue.description,
            "documents": issue.documents,
            "evidence": issue.evidence,
            "recommendation": issue.recommendation,
            "stage_gate": issue.stage_gate,
            "source": "local_analysis",
        })

    # Add Gemini-discovered issues
    for issue in gemini_result.get("cross_document_issues", []):
        issue["source"] = "ai_analysis"
        combined_issues.append(issue)

    # ── Build final output ──
    total = len(combined_issues)
    high = sum(1 for i in combined_issues if i.get("severity") == "HIGH")
    medium = sum(1 for i in combined_issues if i.get("severity") == "MEDIUM")
    low = total - high - medium

    # Compute consistency score: start at 100, deduct per issue
    consistency = max(0, 100 - (high * 15) - (medium * 8) - (low * 3))

    result = {
        "cross_document_issues": combined_issues,
        "cross_reference_matrix": gemini_result.get("cross_reference_matrix", []),
        "consistency_score": consistency,
        "summary": gemini_result.get("summary", ""),
        "total_issues": total,
        "high_severity_count": high,
        "medium_severity_count": medium,
        "low_severity_count": low,
        "entity_extraction": {
            filename: {
                "fields": [e.value for e in entities if e.entity_type == "field_name"],
                "dates": [e.value for e in entities if e.entity_type == "date"],
                "metrics": [e.value for e in entities if e.entity_type == "metric"],
            }
            for filename, entities in all_entities.items()
        },
    }

    print(f"\n  Cross-Document Intelligence Complete:")
    print(f"    Total issues:     {total}")
    print(f"    High severity:    {high}")
    print(f"    Medium severity:  {medium}")
    print(f"    Low severity:     {low}")
    print(f"    Consistency:      {consistency}%")

    return result
