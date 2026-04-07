#!/usr/bin/env python3
"""
RED DUKE — Document Ingestion & Parsing Demo
=============================================
AI-Powered Client Documentation Pipeline
Smart Data Solutions Capstone Project

Run:  python main.py

This script demonstrates that our ingestion pipeline can:
  1. Discover all documents in a client SharePoint folder
  2. Parse every supported file type into structured text
  3. Extract metadata, sections, tables, and workflow elements
  4. Chunk documents for downstream vector embedding (RAG)
  5. Generate an audit checklist mapping artifacts to evidence

Author: Sannidhya Tiwari, Project Lead
"""

# ── Auto-install dependencies if missing ──
import subprocess, sys

def _ensure_deps():
    required = {
        "docx": "python-docx",
        "openpyxl": "openpyxl",
        "pptx": "python-pptx",
        "requests": "requests",
        "dotenv": "python-dotenv",
    }
    missing = []
    for import_name, pip_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"  Installing dependencies: {', '.join(missing)} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )
        print("  Done.\n")

_ensure_deps()
# ── End auto-install ──

import io
import os
import csv
import json
import email
import hashlib
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree
from dataclasses import dataclass, field
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass  # _ensure_deps() will install python-dotenv on next run

# Optional SharePoint integration
try:
    import sharepoint_files as _sp
    _SP_AVAILABLE = True
except ImportError:
    _sp = None  # type: ignore[assignment]
    _SP_AVAILABLE = False

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

_sp_download_dir = os.getenv("SP_DOWNLOAD_DIR", "downloads")
if not os.path.isabs(_sp_download_dir):
    _sp_download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), _sp_download_dir)
DOWNLOAD_DIR = _sp_download_dir

SUPPORTED_EXTENSIONS = {
    ".docx", ".xlsx", ".xlsm", ".pptx", ".pdf", ".vsdx",
    ".csv", ".tsv", ".txt", ".md", ".png", ".jpg", ".jpeg",
}

# ══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ParseResult:
    filename: str
    filepath: str
    file_type: str
    file_size: int
    text: str = ""
    sections: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    @property
    def word_count(self) -> int:
        return len(self.text.split()) if self.text else 0

    @property
    def char_count(self) -> int:
        return len(self.text) if self.text else 0


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_file: str
    section_title: str = ""
    chunk_index: int = 0
    token_estimate: int = 0


# ══════════════════════════════════════════════════════════════════════════════
# PARSERS
# ══════════════════════════════════════════════════════════════════════════════

def parse_docx(filepath: str) -> ParseResult:
    """Parse Word documents — extract paragraphs, headings, tables."""
    import docx

    doc = docx.Document(filepath)
    name = os.path.basename(filepath)

    sections = []
    current = {"title": "Document Content", "lines": []}
    all_lines = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower()
        if "heading" in style:
            if current["lines"]:
                sections.append({"title": current["title"], "content": "\n".join(current["lines"])})
            current = {"title": text, "lines": []}
            all_lines.append(f"\n## {text}")
        else:
            current["lines"].append(text)
            all_lines.append(text)

    if current["lines"]:
        sections.append({"title": current["title"], "content": "\n".join(current["lines"])})

    # Tables
    tables = []
    for i, table in enumerate(doc.tables):
        rows = []
        for row in table.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        if rows:
            tables.append(rows)
            all_lines.append(f"\n[Table {i+1}: {len(rows)} rows x {len(rows[0])} cols]")
            for row in rows[:3]:
                all_lines.append(" | ".join(row))

    props = doc.core_properties
    return ParseResult(
        filename=name, filepath=filepath, file_type="Word Document (.docx)",
        file_size=os.path.getsize(filepath),
        text="\n".join(all_lines),
        sections=sections, tables=tables,
        metadata={
            "author": props.author or "N/A",
            "title": props.title or "N/A",
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables),
            "heading_count": sum(1 for p in doc.paragraphs if "heading" in (p.style.name or "").lower()),
        },
    )


def parse_xlsx(filepath: str) -> ParseResult:
    """Parse Excel workbooks — extract all sheets, rows, structure."""
    import openpyxl
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    wb = openpyxl.load_workbook(filepath, data_only=True)
    name = os.path.basename(filepath)
    all_lines = []
    sections = []
    tables = []
    total_rows = 0
    total_data_cells = 0

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        all_lines.append(f"\n{'='*50}")
        all_lines.append(f"SHEET: {sheet_name} ({ws.max_row} rows x {ws.max_column} cols)")
        all_lines.append(f"{'='*50}")

        sheet_rows = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() if c is not None else "" for c in row]
            if any(cells):
                sheet_rows.append(cells)
                total_data_cells += sum(1 for c in cells if c)

        total_rows += len(sheet_rows)

        if sheet_rows:
            headers = sheet_rows[0]
            all_lines.append("Headers: " + " | ".join(headers))
            for row in sheet_rows[1:]:
                all_lines.append(" | ".join(row))
            tables.append({"sheet": sheet_name, "headers": headers, "row_count": len(sheet_rows) - 1})

        sections.append({
            "title": f"Sheet: {sheet_name}",
            "content": "\n".join(" | ".join(r) for r in sheet_rows) if sheet_rows else "(empty)",
        })

    return ParseResult(
        filename=name, filepath=filepath, file_type="Excel Workbook (.xlsx)",
        file_size=os.path.getsize(filepath),
        text="\n".join(all_lines),
        sections=sections, tables=tables,
        metadata={
            "sheet_count": len(wb.sheetnames),
            "sheet_names": wb.sheetnames,
            "total_data_rows": total_rows,
            "total_data_cells": total_data_cells,
        },
    )


def parse_pptx(filepath: str) -> ParseResult:
    """Parse PowerPoint presentations — extract slides, text, notes, tables."""
    from pptx import Presentation

    prs = Presentation(filepath)
    name = os.path.basename(filepath)
    all_lines = []
    sections = []
    total_shapes = 0
    total_tables = 0

    for i, slide in enumerate(prs.slides, 1):
        slide_lines = []
        all_lines.append(f"\n{'─'*40}")
        all_lines.append(f"SLIDE {i}")
        all_lines.append(f"{'─'*40}")

        for shape in slide.shapes:
            total_shapes += 1
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        slide_lines.append(text)
                        all_lines.append(text)

            if shape.has_table:
                total_tables += 1
                table = shape.table
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    slide_lines.append(row_text)
                    all_lines.append(f"  [TABLE] {row_text}")

        # Speaker notes
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_lines.append(f"[Notes]: {notes}")
                all_lines.append(f"  [NOTES]: {notes}")

        sections.append({"title": f"Slide {i}", "content": "\n".join(slide_lines)})

    return ParseResult(
        filename=name, filepath=filepath, file_type="PowerPoint Presentation (.pptx)",
        file_size=os.path.getsize(filepath),
        text="\n".join(all_lines),
        sections=sections,
        metadata={
            "slide_count": len(prs.slides),
            "total_shapes": total_shapes,
            "tables_in_slides": total_tables,
        },
    )


def parse_vsdx(filepath: str) -> ParseResult:
    """Parse Visio diagrams — extract workflow text from shapes across all pages."""
    name = os.path.basename(filepath)
    all_lines = []
    sections = []
    total_shapes = 0

    with zipfile.ZipFile(filepath) as zf:
        page_files = sorted(
            f for f in zf.namelist()
            if f.startswith("visio/pages/page") and f.endswith(".xml")
        )

        for page_file in page_files:
            page_name = Path(page_file).stem.replace("page", "Page ")
            all_lines.append(f"\n{'─'*40}")
            all_lines.append(f"WORKFLOW {page_name.upper()}")
            all_lines.append(f"{'─'*40}")

            xml_content = zf.read(page_file)
            tree = ElementTree.fromstring(xml_content)
            page_texts = []

            for el in tree.iter():
                if el.tag.endswith("}Text") or el.tag == "Text":
                    text = "".join(el.itertext()).strip()
                    if text:
                        page_texts.append(text)
                        total_shapes += 1

            for t in page_texts:
                all_lines.append(f"  [{t}]")

            # Build a workflow narrative
            if page_texts:
                narrative = " → ".join(page_texts[:20])
                all_lines.append(f"\n  Flow: {narrative}")

            sections.append({
                "title": f"Workflow {page_name}",
                "content": "\n".join(page_texts),
            })

    return ParseResult(
        filename=name, filepath=filepath, file_type="Visio Diagram (.vsdx)",
        file_size=os.path.getsize(filepath),
        text="\n".join(all_lines),
        sections=sections,
        metadata={
            "page_count": len(page_files),
            "total_workflow_nodes": total_shapes,
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHUNKER
# ══════════════════════════════════════════════════════════════════════════════

def chunk_document(result: ParseResult, max_tokens: int = 800, overlap: int = 100) -> list[Chunk]:
    """Chunk a parsed document using section-aware strategy."""
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap * chars_per_token
    chunks = []

    if result.sections:
        for section in result.sections:
            title = section.get("title", "")
            content = section.get("content", "")
            if not content.strip():
                continue

            full_text = f"[{title}]\n{content}" if title else content

            if len(full_text) <= max_chars:
                pieces = [full_text]
            else:
                pieces = []
                paragraphs = full_text.split("\n")
                current = ""
                for para in paragraphs:
                    if len(current) + len(para) + 1 <= max_chars:
                        current = f"{current}\n{para}" if current else para
                    else:
                        if current:
                            pieces.append(current)
                        current = para
                if current:
                    pieces.append(current)

            for piece in pieces:
                if len(piece.strip()) < 50:
                    continue
                cid = hashlib.sha256(f"{result.filename}:{len(chunks)}:{piece[:100]}".encode()).hexdigest()[:12]
                chunks.append(Chunk(
                    chunk_id=cid,
                    text=piece.strip(),
                    source_file=result.filename,
                    section_title=title,
                    chunk_index=len(chunks),
                    token_estimate=max(1, len(piece) // chars_per_token),
                ))
    else:
        # Fallback: sliding window
        text = result.text
        step = max_chars - overlap_chars
        for start in range(0, len(text), max(step, 1)):
            piece = text[start:start + max_chars]
            if len(piece.strip()) < 50:
                continue
            cid = hashlib.sha256(f"{result.filename}:{len(chunks)}".encode()).hexdigest()[:12]
            chunks.append(Chunk(
                chunk_id=cid,
                text=piece.strip(),
                source_file=result.filename,
                chunk_index=len(chunks),
                token_estimate=max(1, len(piece) // chars_per_token),
            ))
            if start + max_chars >= len(text):
                break

    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# DISCOVERY & ORCHESTRATION
# ══════════════════════════════════════════════════════════════════════════════

def discover_files(directory: str) -> list[str]:
    """Recursively discover all supported files."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for fname in sorted(filenames):
            ext = Path(fname).suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, fname))
    return files


def parse_file(filepath: str) -> ParseResult:
    """Route a file to the appropriate parser."""
    ext = Path(filepath).suffix.lower()
    name = os.path.basename(filepath)

    try:
        if ext == ".docx":
            return parse_docx(filepath)
        elif ext in (".xlsx", ".xlsm"):
            return parse_xlsx(filepath)
        elif ext == ".pptx":
            return parse_pptx(filepath)
        elif ext == ".vsdx":
            return parse_vsdx(filepath)
        elif ext == ".pdf":
            import fitz
            pdf = fitz.open(filepath)
            text_parts = []
            for page in pdf:
                text_parts.append(page.get_text("text"))
            pdf.close()
            return ParseResult(
                filename=name, filepath=filepath, file_type="PDF Document",
                file_size=os.path.getsize(filepath),
                text="\n".join(text_parts),
                metadata={"page_count": len(pdf)},
            )
        elif ext in (".csv", ".tsv"):
            delimiter = "\t" if ext == ".tsv" else ","
            with open(filepath, "r", encoding="utf-8-sig") as f:
                text = f.read()
            return ParseResult(
                filename=name, filepath=filepath, file_type="CSV/TSV",
                file_size=os.path.getsize(filepath), text=text,
            )
        elif ext in (".txt", ".md"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            return ParseResult(
                filename=name, filepath=filepath, file_type="Text File",
                file_size=os.path.getsize(filepath), text=text,
            )
        else:
            return ParseResult(
                filename=name, filepath=filepath, file_type=f"Unsupported ({ext})",
                file_size=os.path.getsize(filepath),
                success=False, error=f"No parser for {ext}",
            )
    except Exception as e:
        return ParseResult(
            filename=name, filepath=filepath, file_type=ext,
            file_size=os.path.getsize(filepath),
            success=False, error=str(e),
        )


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT CHECKLIST GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_audit_checklist(results: list[ParseResult], output_path: str):
    """Generate an evidence-based audit checklist like the SDS Project Audit Checklist.

    Maps discovered artifacts to audit deliverables and flags what exists vs. what's missing.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()

    # ── Sheet 1: Document Evidence Matrix ──
    ws1 = wb.active
    ws1.title = "Document Evidence Matrix"

    # Define audit requirements (modeled from the real Project_Audit_Checklist.xlsx)
    audit_requirements = [
        {
            "deliverable": "Business Requirements Document (BRD)",
            "responsibility": "Business Analyst",
            "stage_gate": "Design (TG0)",
            "relevance": "HITRUST / SOC2",
            "keywords": ["brd", "business requirement", "requirement"],
            "control": "Supports HITRUST Control & SOC BRD.1",
        },
        {
            "deliverable": "High-Level Project Plan / Critical Path",
            "responsibility": "PM",
            "stage_gate": "Initiation (TG-1)",
            "relevance": "SOC2",
            "keywords": ["project plan", "critical path", "roadmap", "timeline", "initiation"],
            "control": "Supports SOC Control 1.4",
        },
        {
            "deliverable": "Client Kickoff / Scope Presentation",
            "responsibility": "PM",
            "stage_gate": "Initiation (TG-1)",
            "relevance": "SOC2",
            "keywords": ["kickoff", "scope review", "agenda", "introductions"],
            "control": "Supports SOC Control 1.2",
        },
        {
            "deliverable": "Workflow Diagram / Process Flow",
            "responsibility": "Engineering",
            "stage_gate": "Design (TG0)",
            "relevance": "HITRUST",
            "keywords": ["workflow", "diagram", "process flow", "data capture", "image import"],
            "control": "Supports HITRUST Control 2.16",
        },
        {
            "deliverable": "Implementation / Transition Workbook",
            "responsibility": "PM / Engineering",
            "stage_gate": "Implementation (TG1)",
            "relevance": "HITRUST / SOC2",
            "keywords": ["transition", "workbook", "implementation", "configuration", "sop"],
            "control": "Supports HITRUST Change Management",
        },
        {
            "deliverable": "Reporting Requirements & SLA Documentation",
            "responsibility": "PM",
            "stage_gate": "Implementation (TG1)",
            "relevance": "SOC2",
            "keywords": ["report", "reporting", "sla", "volume", "frequency"],
            "control": "Supports SOC Control 3.1",
        },
        {
            "deliverable": "Testing Evidence / UAT Sign-off",
            "responsibility": "Engineering",
            "stage_gate": "Test (TG2)",
            "relevance": "HITRUST",
            "keywords": ["testing", "uat", "test case", "functional testing", "volume testing"],
            "control": "Supports HITRUST Control 6.18a",
        },
        {
            "deliverable": "Security & Access Control Documentation",
            "responsibility": "Engineering",
            "stage_gate": "Initiation (TG-1)",
            "relevance": "HITRUST",
            "keywords": ["security", "access control", "sso", "single sign-on", "password"],
            "control": "Supports HITRUST Access Control",
        },
        {
            "deliverable": "Eligibility / Claims Configuration",
            "responsibility": "Engineering",
            "stage_gate": "Implementation (TG1)",
            "relevance": "SOC2",
            "keywords": ["eligibility", "claim", "matching", "reject", "routing", "837"],
            "control": "Supports SOC Controls 5.1-5.5",
        },
        {
            "deliverable": "M2P / Go-Live Sign-off",
            "responsibility": "PM / Tech Lead",
            "stage_gate": "Deploy/Warranty (TG3)",
            "relevance": "HITRUST / SOC2",
            "keywords": ["m2p", "go-live", "move to production", "sign-off", "warranty"],
            "control": "Supports HITRUST Control 6.18b",
        },
        {
            "deliverable": "TPM / Compliance Checklist",
            "responsibility": "PM / Engineer",
            "stage_gate": "Test (TG2)",
            "relevance": "HITRUST",
            "keywords": ["tpm", "checklist", "compliance", "complete?"],
            "control": "Supports Internal Compliance Review",
        },
        {
            "deliverable": "Training & Process Awareness Documentation",
            "responsibility": "PM",
            "stage_gate": "Initiation (TG-1)",
            "relevance": "HITRUST",
            "keywords": ["training", "process awareness", "onboarding"],
            "control": "Supports HITRUST Training Requirement",
        },
    ]

    # Match artifacts to requirements
    for req in audit_requirements:
        matching_files = []
        matching_evidence = []
        for r in results:
            if not r.success:
                continue
            combined_text = (r.text + " " + r.filename).lower()
            for kw in req["keywords"]:
                if kw.lower() in combined_text:
                    matching_files.append(r.filename)
                    # Find a snippet
                    idx = combined_text.find(kw.lower())
                    start = max(0, idx - 30)
                    end = min(len(combined_text), idx + len(kw) + 60)
                    snippet = combined_text[start:end].strip().replace("\n", " ")
                    matching_evidence.append(f'"{snippet}"')
                    break

        req["found_files"] = list(set(matching_files))
        req["evidence_snippets"] = list(set(matching_evidence))[:2]
        req["status"] = "FOUND" if matching_files else "MISSING"

    # Write headers
    headers = [
        "Audit Deliverable", "Responsibility", "Stage Gate",
        "Audit Relevance", "Status", "Evidence File(s)",
        "Evidence Snippet", "Control Activity",
    ]
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    found_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    missing_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border

    # Write data
    for row_idx, req in enumerate(audit_requirements, 2):
        values = [
            req["deliverable"],
            req["responsibility"],
            req["stage_gate"],
            req["relevance"],
            req["status"],
            "\n".join(req["found_files"]) if req["found_files"] else "—",
            "\n".join(req["evidence_snippets"]) if req["evidence_snippets"] else "—",
            req["control"],
        ]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=row_idx, column=col, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = thin_border

        # Color the status cell
        status_cell = ws1.cell(row=row_idx, column=5)
        status_cell.font = Font(bold=True)
        if req["status"] == "FOUND":
            status_cell.fill = found_fill
        else:
            status_cell.fill = missing_fill

    # Column widths
    widths = [35, 18, 20, 15, 10, 40, 50, 30]
    for i, w in enumerate(widths, 1):
        ws1.column_dimensions[chr(64 + i)].width = w

    # ── Sheet 2: Parsed Files Summary ──
    ws2 = wb.create_sheet("Parsed Files Summary")
    sum_headers = ["Filename", "File Type", "Size (KB)", "Words", "Sections", "Tables", "Parse Status"]
    for col, h in enumerate(sum_headers, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    for row_idx, r in enumerate(results, 2):
        vals = [
            r.filename,
            r.file_type,
            f"{r.file_size / 1024:.1f}",
            str(r.word_count),
            str(len(r.sections)),
            str(len(r.tables)),
            "OK" if r.success else f"FAIL: {r.error}",
        ]
        for col, val in enumerate(vals, 1):
            cell = ws2.cell(row=row_idx, column=col, value=val)
            cell.alignment = Alignment(wrap_text=True)
            cell.border = thin_border

    widths2 = [45, 25, 10, 10, 10, 10, 20]
    for i, w in enumerate(widths2, 1):
        ws2.column_dimensions[chr(64 + i)].width = w

    # ── Sheet 3: Gap Analysis ──
    ws3 = wb.create_sheet("Gap Analysis")
    gap_headers = ["Missing Deliverable", "Stage Gate", "Risk Level", "Recommendation"]
    for col, h in enumerate(gap_headers, 1):
        cell = ws3.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    gap_row = 2
    for req in audit_requirements:
        if req["status"] == "MISSING":
            vals = [
                req["deliverable"],
                req["stage_gate"],
                "HIGH" if "HITRUST" in req["relevance"] else "MEDIUM",
                f"Obtain {req['deliverable'].lower()} from {req['responsibility']} before {req['stage_gate']} gate.",
            ]
            for col, val in enumerate(vals, 1):
                cell = ws3.cell(row=gap_row, column=col, value=val)
                cell.alignment = Alignment(wrap_text=True)
                cell.border = thin_border
                if col == 3 and val == "HIGH":
                    cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    cell.font = Font(bold=True)
            gap_row += 1

    if gap_row == 2:
        ws3.cell(row=2, column=1, value="No gaps found — all audit deliverables have evidence.").font = Font(italic=True)

    widths3 = [40, 22, 12, 55]
    for i, w in enumerate(widths3, 1):
        ws3.column_dimensions[chr(64 + i)].width = w

    wb.save(output_path)
    return audit_requirements


# ══════════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def print_header(text, char="═"):
    width = 80
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def print_subheader(text, char="─"):
    print(f"\n  {char * 60}")
    print(f"  {text}")
    print(f"  {char * 60}")


def print_parse_result(result: ParseResult):
    """Print a detailed parse report for a single document."""
    print_subheader(f"📄 {result.filename}")
    print(f"  Type:       {result.file_type}")
    print(f"  Size:       {result.file_size / 1024:.1f} KB")
    print(f"  Parsed:     {'✅ SUCCESS' if result.success else '❌ FAILED: ' + str(result.error)}")
    print(f"  Words:      {result.word_count:,}")
    print(f"  Characters: {result.char_count:,}")
    print(f"  Sections:   {len(result.sections)}")
    print(f"  Tables:     {len(result.tables)}")

    if result.metadata:
        print(f"\n  Metadata:")
        for k, v in result.metadata.items():
            if isinstance(v, list) and len(v) > 5:
                v = f"{v[:5]} ... ({len(v)} total)"
            print(f"    {k}: {v}")

    if result.sections:
        print(f"\n  Section Breakdown:")
        for i, s in enumerate(result.sections):
            content = s.get("content", "")
            words = len(content.split())
            preview = content[:100].replace("\n", " ").strip()
            print(f"    {i+1}. [{s['title']}] — {words} words")
            print(f"       Preview: \"{preview}...\"")

    # Show a content sample
    if result.text:
        sample = result.text[:300].replace("\n", "\n       ")
        print(f"\n  Content Sample:")
        print(f"       {sample}...")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print_header("RED DUKE — Document Ingestion & Parsing Demo")
    print("  AI-Powered Client Documentation Pipeline")
    print("  Smart Data Solutions Capstone Project")
    print(f"  Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Step 0: SharePoint Download (optional) ──
    source_dir = SAMPLE_DATA_DIR
    if _SP_AVAILABLE and _sp.is_sharepoint_configured():
        print_header("STEP 0: SHAREPOINT DOWNLOAD", "─")
        try:
            source_dir = _sp.download_from_sharepoint(DOWNLOAD_DIR)
            file_count = len(discover_files(source_dir))
            print(f"\n  Downloaded to: {source_dir}")
            print(f"  Files ready:   {file_count}")
        except Exception as exc:
            print(f"\n  SharePoint download failed: {exc}")
            print("  Falling back to local sample_data/")
            source_dir = SAMPLE_DATA_DIR
    else:
        print(f"\n  SharePoint not configured — using local sample_data/")

    # ── Step 1: Discover ──
    print_header("STEP 1: DOCUMENT DISCOVERY", "─")
    files = discover_files(source_dir)
    print(f"\n  📁 Scanning: {source_dir}")
    print(f"  📄 Found {len(files)} supported documents:\n")
    for f in files:
        rel = os.path.relpath(f, source_dir)
        size = os.path.getsize(f) / 1024
        print(f"    • {rel} ({size:.1f} KB)")

    # ── Step 2: Parse ──
    print_header("STEP 2: DOCUMENT PARSING", "─")
    results: list[ParseResult] = []
    for filepath in files:
        result = parse_file(filepath)
        results.append(result)
        print_parse_result(result)

    # ── Step 3: Chunk ──
    print_header("STEP 3: CHUNKING FOR VECTOR EMBEDDING (RAG)", "─")
    all_chunks: list[Chunk] = []
    for result in results:
        if result.success:
            chunks = chunk_document(result)
            all_chunks.extend(chunks)
            print(f"\n  {result.filename}: {len(chunks)} chunks")
            for c in chunks[:3]:
                preview = c.text[:80].replace("\n", " ")
                print(f"    Chunk {c.chunk_index} [{c.section_title}] ~{c.token_estimate} tokens: \"{preview}...\"")
            if len(chunks) > 3:
                print(f"    ... and {len(chunks) - 3} more chunks")

    print(f"\n  ══════════════════════════════════════")
    print(f"  TOTAL CHUNKS: {len(all_chunks)}")
    total_tokens = sum(c.token_estimate for c in all_chunks)
    print(f"  TOTAL TOKENS: ~{total_tokens:,}")
    print(f"  AVG TOKENS/CHUNK: ~{total_tokens // max(len(all_chunks), 1)}")
    print(f"  ══════════════════════════════════════")

    # ── Step 4: Audit Checklist ──
    print_header("STEP 4: AUDIT EVIDENCE CHECKLIST GENERATION", "─")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    checklist_path = os.path.join(OUTPUT_DIR, "Client_Audit_Checklist.xlsx")
    audit_reqs = generate_audit_checklist(results, checklist_path)

    found_count = sum(1 for r in audit_reqs if r["status"] == "FOUND")
    missing_count = sum(1 for r in audit_reqs if r["status"] == "MISSING")

    print(f"\n  Generated: {checklist_path}")
    print(f"\n  Audit Evidence Summary:")
    print(f"  {'─' * 55}")
    print(f"  {'Deliverable':<40} {'Status':<10}")
    print(f"  {'─' * 55}")
    for req in audit_reqs:
        icon = "✅" if req["status"] == "FOUND" else "❌"
        print(f"  {icon} {req['deliverable']:<38} {req['status']:<10}")
        if req["found_files"]:
            for f in req["found_files"]:
                print(f"     └─ {f}")
    print(f"  {'─' * 55}")
    print(f"  FOUND: {found_count}/{len(audit_reqs)}  |  MISSING: {missing_count}/{len(audit_reqs)}")
    print(f"  Coverage: {found_count / len(audit_reqs) * 100:.0f}%")

    # ── Save chunk data ──
    chunks_path = os.path.join(OUTPUT_DIR, "chunks.jsonl")
    with open(chunks_path, "w") as f:
        for c in all_chunks:
            f.write(json.dumps({
                "chunk_id": c.chunk_id,
                "text": c.text,
                "source_file": c.source_file,
                "section_title": c.section_title,
                "chunk_index": c.chunk_index,
                "token_estimate": c.token_estimate,
            }) + "\n")

    # ── Step 5: AI-Powered Deep Analysis (Gemini) ──
    print_header("STEP 5: AI-POWERED DEEP ANALYSIS (GEMINI)", "─")
    analysis_output = None
    try:
        from analyzer import analyze_documents
        analysis_output = analyze_documents(results)

        # Attach pipeline metadata
        analysis_output["pipeline_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "source_directory": source_dir,
            "total_chunks": len(all_chunks),
            "total_tokens": total_tokens,
            "parse_failures": sum(1 for r in results if not r.success),
        }

        # Write to output dir
        analysis_json_path = os.path.join(OUTPUT_DIR, "analysis_output.json")
        with open(analysis_json_path, "w", encoding="utf-8") as f:
            json.dump(analysis_output, f, indent=2)

        # Also write to frontend/public/ so React can fetch it
        frontend_public = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public"
        )
        os.makedirs(frontend_public, exist_ok=True)
        frontend_json_path = os.path.join(frontend_public, "analysis_output.json")
        with open(frontend_json_path, "w", encoding="utf-8") as f:
            json.dump(analysis_output, f, indent=2)

        # Generate Excel report
        from analyzer import export_excel
        excel_path = os.path.join(OUTPUT_DIR, "Red_Duke_Report.xlsx")
        export_excel(analysis_output, excel_path)

        # Copy Excel to frontend/public so it can be downloaded from the UI
        import shutil
        frontend_excel = os.path.join(frontend_public, "Red_Duke_Report.xlsx")
        shutil.copy2(excel_path, frontend_excel)

        m = analysis_output.get("metrics", {})
        print(f"\n  Coverage score:    {m.get('coverage_score', '?')}%")
        print(f"  Total gaps:        {m.get('total_gaps', '?')}")
        print(f"  High-risk gaps:    {m.get('high_risk_gaps', '?')}")
        print(f"  Output (backend):  {analysis_json_path}")
        print(f"  Output (frontend): {frontend_json_path}")
        print(f"  Excel report:      {excel_path}")

    except Exception as exc:
        print(f"\n  AI Analysis failed: {exc}")
        import traceback
        traceback.print_exc()
        print("  Building fallback analysis from audit data...")

        # Build a minimal analysis_output from audit checklist so Steps 6/7 can still run
        analysis_output = {
            "client_overview": {
                "client_name": "Client",
                "summary": "AI analysis failed — showing audit-only data.",
                "scope": "",
                "integrations": [],
                "key_decisions": [],
                "open_risks": [],
                "current_phase": "Unknown",
            },
            "documents": [
                {
                    "filename": r.filename,
                    "file_type": r.file_type,
                    "word_count": r.word_count,
                    "quality_score": "ADEQUATE",
                }
                for r in results if r.success
            ],
            "workflow_narrative": {},
            "checklist": [],
            "gap_analysis": [],
            "metrics": {
                "coverage_score": 0,
                "total_gaps": 0,
                "high_risk_gaps": 0,
            },
            "pipeline_metadata": {
                "generated_at": datetime.now().isoformat(),
                "source_directory": source_dir,
                "total_chunks": len(all_chunks),
                "total_tokens": total_tokens,
                "parse_failures": sum(1 for r in results if not r.success),
                "ai_analysis_failed": True,
            },
        }

    # ── Step 6: Cross-Document Intelligence ──
    print_header("STEP 6: CROSS-DOCUMENT INTELLIGENCE", "─")
    try:
        from cross_document_intel import run_cross_document_analysis
        cross_intel = run_cross_document_analysis(results)

        # Attach to analysis output so the frontend can consume it
        if analysis_output is not None:
            analysis_output["cross_document_intel"] = cross_intel

            # Re-write the analysis JSON with cross-intel included
            analysis_json_path = os.path.join(OUTPUT_DIR, "analysis_output.json")
            with open(analysis_json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_output, f, indent=2)

            frontend_public = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public"
            )
            frontend_json_path = os.path.join(frontend_public, "analysis_output.json")
            with open(frontend_json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_output, f, indent=2)

            # Re-generate Excel with the cross-intel sheet
            from analyzer import export_excel
            excel_path = os.path.join(OUTPUT_DIR, "Red_Duke_Report.xlsx")
            export_excel(analysis_output, excel_path)

            import shutil
            frontend_excel = os.path.join(frontend_public, "Red_Duke_Report.xlsx")
            shutil.copy2(excel_path, frontend_excel)

            print(f"\n  Cross-intel merged into analysis_output.json")

    except Exception as exc:
        print(f"\n  Cross-Document Intelligence failed: {exc}")
        import traceback
        traceback.print_exc()

    # ── Step 7: Project Intelligence ("The Brain") ──
    print_header("STEP 7: PROJECT INTELLIGENCE ENGINE", "─")
    try:
        from project_intelligence import run_project_intelligence
        intel = run_project_intelligence(
            analysis_output or {},
            analysis_output.get("cross_document_intel") if analysis_output else {},
            results,
        )

        if analysis_output is not None:
            # Replace checklist with scored version
            analysis_output["checklist"] = intel["scored_checklist"]
            analysis_output["stage_readiness"] = intel["stage_readiness"]
            analysis_output["gate_decisions"] = intel["gate_decisions"]
            analysis_output["proactive_actions"] = intel["proactive_actions"]
            analysis_output["project_mind"] = intel["project_mind"]
            analysis_output["overall_readiness_score"] = intel["overall_readiness_score"]

            # Final write of analysis JSON
            analysis_json_path = os.path.join(OUTPUT_DIR, "analysis_output.json")
            with open(analysis_json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_output, f, indent=2)

            frontend_public = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public"
            )
            frontend_json_path = os.path.join(frontend_public, "analysis_output.json")
            with open(frontend_json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_output, f, indent=2)

            # Final Excel regeneration
            from analyzer import export_excel
            excel_path = os.path.join(OUTPUT_DIR, "Red_Duke_Report.xlsx")
            export_excel(analysis_output, excel_path)

            import shutil
            frontend_excel = os.path.join(frontend_public, "Red_Duke_Report.xlsx")
            shutil.copy2(excel_path, frontend_excel)

            print(f"\n  Intelligence merged into analysis_output.json")

    except Exception as exc:
        print(f"\n  Project Intelligence failed: {exc}")
        import traceback
        traceback.print_exc()

    # ── Step 8: Upload Outputs to SharePoint (optional) ──
    if _SP_AVAILABLE and _sp.is_sharepoint_configured():
        print_header("STEP 8: SHAREPOINT UPLOAD", "─")
        try:
            uploaded = _sp.upload_to_sharepoint(OUTPUT_DIR)
            print(f"\n  Uploaded {len(uploaded)} file(s) to SharePoint ✅")
        except Exception as exc:
            print(f"\n  SharePoint upload failed: {exc}")

    # ── Final Summary ──
    print_header("PIPELINE COMPLETE ✅")
    print(f"  Documents discovered:  {len(files)}")
    print(f"  Documents parsed:      {sum(1 for r in results if r.success)}/{len(results)}")
    print(f"  Parse failures:        {sum(1 for r in results if not r.success)}")
    print(f"  Total chunks:          {len(all_chunks)}")
    print(f"  Total tokens:          ~{total_tokens:,}")
    print(f"  Audit coverage:        {found_count}/{len(audit_reqs)} ({found_count/len(audit_reqs)*100:.0f}%)")
    print(f"\n  Output files:")
    print(f"    • {checklist_path}")
    print(f"    • {chunks_path}")
    print(f"\n{'═' * 80}")

    return results, all_chunks


if __name__ == "__main__":
    results, chunks = main()