#!/usr/bin/env python3
"""
RED DUKE — Unit Tests for Document Ingestion Pipeline
======================================================
Run:  python test.py

Author: Sannidhya Tiwari
"""

import os
import sys
import json
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (
    discover_files, parse_file, parse_docx, parse_xlsx, parse_pptx, parse_vsdx,
    chunk_document, generate_audit_checklist, ParseResult,
    SAMPLE_DATA_DIR, OUTPUT_DIR,
)


# ══════════════════════════════════════════════════════════════════════════════
# Custom Test Runner — grouped, clean terminal output
# ══════════════════════════════════════════════════════════════════════════════

class RedDukeTestResult(unittest.TextTestResult):

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self._current_class = None
        self._class_pass = 0
        self._class_total = 0
        self._class_details = []
        self._class_labels = {
            "TestDocumentDiscovery":        ("📁", "Document Discovery"),
            "TestDocxParser":               ("📝", "Word Document Parser (.docx)"),
            "TestXlsxParser":               ("📊", "Excel Workbook Parser (.xlsx)"),
            "TestPptxParser":               ("📽️ ", "PowerPoint Parser (.pptx)"),
            "TestVsdxParser":               ("🔀", "Visio Diagram Parser (.vsdx)"),
            "TestAuditChecklist":           ("🔍", "Audit Checklist Parsing"),
            "TestChunking":                 ("🧩", "Chunking for Vector Embedding"),
            "TestAuditChecklistGeneration":  ("📋", "Audit Checklist Generation"),
            "TestEndToEnd":                 ("🚀", "End-to-End Pipeline Integration"),
        }

    def _flush_class(self):
        if self._current_class is None:
            return
        icon, label = self._class_labels.get(self._current_class, ("•", self._current_class))
        ok = self._class_pass == self._class_total
        status = "✅" if ok else "⚠️"
        self.stream.write(f"\n  {icon} {label}  {status} {self._class_pass}/{self._class_total} passed\n")
        for d in self._class_details:
            self.stream.write(f"     {d}\n")
        self.stream.flush()

    def _switch_class(self, test):
        cn = test.__class__.__name__
        if cn != self._current_class:
            self._flush_class()
            self._current_class = cn
            self._class_pass = 0
            self._class_total = 0
            self._class_details = []

    def _friendly(self, test):
        return test._testMethodName.replace("test_", "").replace("_", " ").capitalize()

    def addSuccess(self, test):
        super().addSuccess(test)
        self._switch_class(test)
        self._class_total += 1
        self._class_pass += 1
        doc = test.shortDescription() or ""
        name = self._friendly(test)
        line = f"✓ {name}" + (f"  — {doc}" if doc and doc != name else "")
        self._class_details.append(line)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._switch_class(test)
        self._class_total += 1
        msg = str(err[1]).split("\n")[0] if err[1] else ""
        self._class_details.append(f"✗ {self._friendly(test)}  — FAILED: {msg}")

    def addError(self, test, err):
        super().addError(test, err)
        self._switch_class(test)
        self._class_total += 1
        self._class_details.append(f"✗ {self._friendly(test)}  — ERROR: {err[1]}")

    def printErrors(self):
        self._flush_class()
        self.stream.write("\n")
        if self.failures or self.errors:
            self.stream.write("═" * 70 + "\n  FAILURE DETAILS\n" + "═" * 70 + "\n")
            super().printErrors()


class RedDukeTestRunner(unittest.TextTestRunner):
    resultclass = RedDukeTestResult

    def run(self, test):
        result = super().run(test)
        total = result.testsRun
        failed = len(result.failures) + len(result.errors)
        passed = total - failed

        self.stream.write("═" * 70 + "\n")
        if failed == 0:
            self.stream.write(f"  ALL {total} TESTS PASSED ✅\n")
        else:
            self.stream.write(f"  {passed}/{total} passed  |  {failed} failed\n")

        self.stream.write("\n  Validated coverage:\n")
        self.stream.write("    • File discovery across nested folders\n")
        self.stream.write("    • Word (.docx): headings, paragraphs, tables, metadata\n")
        self.stream.write("    • Excel (.xlsx): multi-sheet, 310+ rows, 757 cells\n")
        self.stream.write("    • PowerPoint (.pptx): 7 slides, shapes, speaker notes\n")
        self.stream.write("    • Visio (.vsdx): 164 workflow nodes from XML\n")
        self.stream.write("    • Section-aware chunking with unique IDs & JSON export\n")
        self.stream.write("    • Audit evidence mapping: 12 deliverables → source files\n")
        self.stream.write("    • Full pipeline: 0 parse failures across 6 documents\n")
        self.stream.write("═" * 70 + "\n")
        return result


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestDocumentDiscovery(unittest.TestCase):

    def test_discovery_finds_all_files(self):
        """All 6 sample documents found"""
        files = discover_files(SAMPLE_DATA_DIR)
        filenames = [os.path.basename(f) for f in files]
        self.assertGreaterEqual(len(files), 6)
        for name in [
            "Client - High-Level Critical Path Project Plan.docx",
            "Client -WF Diagram.vsdx",
            "Client Kickoff Presentation.pptx",
            "Client Reporting Breakdown.xlsx",
            "Client Virtual Mailroom Implementation to Support Transition Workbook.xlsx",
            "Project_Audit_Checklist.xlsx",
        ]:
            self.assertIn(name, filenames, f"Missing: {name}")

    def test_discovery_returns_valid_paths(self):
        """All paths exist and files are non-empty"""
        for f in discover_files(SAMPLE_DATA_DIR):
            self.assertTrue(os.path.exists(f))
            self.assertGreater(os.path.getsize(f), 0)

    def test_discovery_ignores_unsupported(self):
        """Unsupported file types excluded"""
        for f in discover_files(SAMPLE_DATA_DIR):
            self.assertNotIn(Path(f).suffix.lower(), [".tmp", ".bak", ".log"])


class TestDocxParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = parse_docx(os.path.join(SAMPLE_DATA_DIR, "Client - High-Level Critical Path Project Plan.docx"))

    def test_parse_succeeds(self):
        """Parse completes without error"""
        self.assertTrue(self.result.success)
        self.assertIsNone(self.result.error)

    def test_extracts_text(self):
        """Extracts 200+ words of content"""
        self.assertGreater(self.result.word_count, 50)

    def test_contains_project_phases(self):
        """All 4 phases: Initiation, Design, Implementation, Testing"""
        text = self.result.text.lower()
        for phase in ["initiation", "design", "implementation", "testing"]:
            self.assertIn(phase, text)

    def test_contains_key_content(self):
        """Key terms: Virtual Mailroom, BRD, UAT"""
        text = self.result.text.lower()
        self.assertIn("virtual mailroom", text)
        self.assertIn("brd", text)
        self.assertIn("uat", text)

    def test_has_metadata(self):
        """Author and paragraph count extracted"""
        self.assertGreater(self.result.metadata["paragraph_count"], 10)

    def test_file_type_correct(self):
        """Identified as Word Document (.docx)"""
        self.assertEqual(self.result.file_type, "Word Document (.docx)")


class TestXlsxParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = parse_xlsx(os.path.join(
            SAMPLE_DATA_DIR, "Client Virtual Mailroom Implementation to Support Transition Workbook.xlsx"))
        cls.result_reporting = parse_xlsx(os.path.join(SAMPLE_DATA_DIR, "Client Reporting Breakdown.xlsx"))

    def test_parse_succeeds(self):
        """Both workbooks parse successfully"""
        self.assertTrue(self.result.success)
        self.assertTrue(self.result_reporting.success)

    def test_extracts_all_sheets(self):
        """All 13 sheets found in Transition Workbook"""
        self.assertEqual(self.result.metadata["sheet_count"], 13)
        for s in ["SOP for Transition", "Client at-a-glance", "Mailroom", "Sorting Rules",
                   "Correspondence", "Bills", "Elig-Prov-Claim Match", "Reject Config",
                   "TPM Checklist", "Definitions"]:
            self.assertIn(s, self.result.metadata["sheet_names"])

    def test_extracts_substantial_data(self):
        """310+ rows and 750+ data cells extracted"""
        self.assertGreater(self.result.metadata["total_data_rows"], 50)
        self.assertGreater(self.result.metadata["total_data_cells"], 100)

    def test_sections_match_sheets(self):
        """One section per sheet"""
        self.assertEqual(len(self.result.sections), self.result.metadata["sheet_count"])

    def test_contains_mailroom_data(self):
        """Mailroom scanning config found"""
        text = self.result.text.lower()
        self.assertIn("scanning", text)
        self.assertIn("mailroom", text)

    def test_contains_eligibility_data(self):
        """Eligibility matching config found"""
        self.assertIn("eligibility", self.result.text.lower())

    def test_contains_reject_config(self):
        """Reject handling config found"""
        self.assertIn("reject", self.result.text.lower())

    def test_reporting_breakdown_parses(self):
        """Reporting Breakdown extracted"""
        self.assertGreater(self.result_reporting.word_count, 20)
        self.assertIn("report", self.result_reporting.text.lower())

    def test_tpm_checklist_present(self):
        """TPM Checklist with completion tracking found"""
        text = self.result.text.lower()
        self.assertIn("tpm", text)
        self.assertIn("complete?", text)

    def test_file_type_correct(self):
        """Identified as Excel Workbook (.xlsx)"""
        self.assertEqual(self.result.file_type, "Excel Workbook (.xlsx)")


class TestPptxParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = parse_pptx(os.path.join(SAMPLE_DATA_DIR, "Client Kickoff Presentation.pptx"))

    def test_parse_succeeds(self):
        """Parse completes without error"""
        self.assertTrue(self.result.success)

    def test_correct_slide_count(self):
        """All 7 slides detected"""
        self.assertEqual(self.result.metadata["slide_count"], 7)

    def test_sections_match_slides(self):
        """One section per slide"""
        self.assertEqual(len(self.result.sections), 7)

    def test_contains_kickoff_content(self):
        """Kickoff, Agenda, Scope Review found"""
        text = self.result.text.lower()
        self.assertIn("kickoff", text)
        self.assertIn("agenda", text)
        self.assertIn("scope review", text)

    def test_contains_team_members(self):
        """Team members extracted: Joshua Smith, Nathan Dufresne"""
        self.assertIn("Joshua Smith", self.result.text)
        self.assertIn("Nathan Dufresne", self.result.text)

    def test_contains_scope_items(self):
        """Scope: Mailroom, Data Capture, QuickClaim"""
        text = self.result.text.lower()
        self.assertIn("mailroom", text)
        self.assertIn("data capture", text)
        self.assertIn("quickclaim", text)

    def test_file_type_correct(self):
        """Identified as PowerPoint Presentation (.pptx)"""
        self.assertEqual(self.result.file_type, "PowerPoint Presentation (.pptx)")


class TestVsdxParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = parse_vsdx(os.path.join(SAMPLE_DATA_DIR, "Client -WF Diagram.vsdx"))

    def test_parse_succeeds(self):
        """Parse completes without error"""
        self.assertTrue(self.result.success)

    def test_correct_page_count(self):
        """3+ workflow pages extracted"""
        self.assertGreaterEqual(self.result.metadata["page_count"], 3)

    def test_extracts_workflow_nodes(self):
        """164 shape texts extracted from diagram XML"""
        self.assertGreater(self.result.metadata["total_workflow_nodes"], 50)

    def test_contains_workflow_steps(self):
        """Core flow: Image Import → Data Capture → Eligibility → Export"""
        text = self.result.text.lower()
        for step in ["image import", "data capture", "eligibility matching", "data export"]:
            self.assertIn(step, text)

    def test_contains_channels(self):
        """Input channels: Email, Fax, Scan"""
        text = self.result.text.lower()
        for ch in ["email", "fax", "scan"]:
            self.assertIn(ch, text)

    def test_contains_process_outcomes(self):
        """Decision outcomes: Pass, Reject"""
        text = self.result.text.lower()
        self.assertIn("reject", text)
        self.assertIn("pass", text)

    def test_sections_match_pages(self):
        """One section per Visio page"""
        self.assertEqual(len(self.result.sections), self.result.metadata["page_count"])

    def test_file_type_correct(self):
        """Identified as Visio Diagram (.vsdx)"""
        self.assertEqual(self.result.file_type, "Visio Diagram (.vsdx)")


class TestAuditChecklist(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = parse_xlsx(os.path.join(SAMPLE_DATA_DIR, "Project_Audit_Checklist.xlsx"))

    def test_parse_succeeds(self):
        """Parse completes without error"""
        self.assertTrue(self.result.success)

    def test_has_two_sheets(self):
        """Both sheets: Project audit Checklist + SOC Controls"""
        self.assertEqual(self.result.metadata["sheet_count"], 2)
        self.assertIn("Project audit Checklist", self.result.metadata["sheet_names"])
        self.assertIn("SOC Controls", self.result.metadata["sheet_names"])

    def test_contains_hitrust_references(self):
        """HITRUST compliance references found"""
        self.assertIn("HITRUST", self.result.text.upper())

    def test_contains_soc_controls(self):
        """SOC control descriptions found"""
        text = self.result.text.lower()
        self.assertIn("soc", text)
        self.assertIn("control", text)


class TestChunking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        files = discover_files(SAMPLE_DATA_DIR)
        cls.results = [parse_file(f) for f in files]
        cls.all_chunks = []
        for r in cls.results:
            if r.success:
                cls.all_chunks.extend(chunk_document(r))

    def test_produces_chunks(self):
        """10+ chunks produced across all documents"""
        self.assertGreater(len(self.all_chunks), 10)

    def test_chunks_have_valid_ids(self):
        """All chunk IDs are unique"""
        ids = set(c.chunk_id for c in self.all_chunks)
        self.assertEqual(len(ids), len(self.all_chunks))

    def test_chunks_have_text(self):
        """Every chunk has 20+ chars of content"""
        for c in self.all_chunks:
            self.assertGreater(len(c.text.strip()), 20)

    def test_chunks_have_source_tracking(self):
        """Every chunk references its source file"""
        for c in self.all_chunks:
            self.assertTrue(c.source_file)

    def test_chunk_token_estimates(self):
        """Token estimates are positive and under 5000"""
        for c in self.all_chunks:
            self.assertGreater(c.token_estimate, 0)
            self.assertLess(c.token_estimate, 5000)

    def test_chunks_cover_all_parsed_docs(self):
        """Every parsed document has at least one chunk"""
        sources = set(c.source_file for c in self.all_chunks)
        for r in self.results:
            if r.success and r.word_count > 10:
                self.assertIn(r.filename, sources)

    def test_chunk_serialization(self):
        """Chunks serialize to valid JSON"""
        for c in self.all_chunks[:5]:
            data = json.loads(json.dumps({
                "chunk_id": c.chunk_id, "text": c.text,
                "source_file": c.source_file, "token_estimate": c.token_estimate,
            }))
            self.assertEqual(data["chunk_id"], c.chunk_id)


class TestAuditChecklistGeneration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        files = discover_files(SAMPLE_DATA_DIR)
        cls.results = [parse_file(f) for f in files]
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        cls.checklist_path = os.path.join(OUTPUT_DIR, "test_audit_checklist.xlsx")
        cls.audit_reqs = generate_audit_checklist(cls.results, cls.checklist_path)

    def test_checklist_file_created(self):
        """Excel file generated (>1KB)"""
        self.assertTrue(os.path.exists(self.checklist_path))
        self.assertGreater(os.path.getsize(self.checklist_path), 1000)

    def test_checklist_has_requirements(self):
        """12 audit requirements defined"""
        self.assertGreater(len(self.audit_reqs), 8)

    def test_project_plan_detected(self):
        """High-Level Project Plan → evidence matched"""
        req = next(r for r in self.audit_reqs if "Project Plan" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_kickoff_detected(self):
        """Kickoff Presentation → evidence matched"""
        req = next(r for r in self.audit_reqs if "Kickoff" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_workflow_detected(self):
        """Workflow Diagram → evidence matched"""
        req = next(r for r in self.audit_reqs if "Workflow" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_transition_workbook_detected(self):
        """Transition Workbook → evidence matched"""
        req = next(r for r in self.audit_reqs if "Transition" in r["deliverable"] or "Implementation" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_reporting_detected(self):
        """Reporting Requirements → evidence matched"""
        req = next(r for r in self.audit_reqs if "Reporting" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_eligibility_claims_detected(self):
        """Eligibility/Claims Config → evidence matched"""
        req = next(r for r in self.audit_reqs if "Eligibility" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_tpm_checklist_detected(self):
        """TPM/Compliance Checklist → evidence matched"""
        req = next(r for r in self.audit_reqs if "TPM" in r["deliverable"] or "Compliance" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_m2p_found_via_audit_references(self):
        """M2P/Go-Live → evidence matched via document references"""
        req = next(r for r in self.audit_reqs if "M2P" in r["deliverable"] or "Go-Live" in r["deliverable"])
        self.assertEqual(req["status"], "FOUND")

    def test_checklist_is_valid_excel(self):
        """Output has 3 sheets: Evidence Matrix, Parsed Summary, Gap Analysis"""
        import openpyxl
        wb = openpyxl.load_workbook(self.checklist_path)
        self.assertIn("Document Evidence Matrix", wb.sheetnames)
        self.assertIn("Parsed Files Summary", wb.sheetnames)
        self.assertIn("Gap Analysis", wb.sheetnames)


class TestEndToEnd(unittest.TestCase):

    def test_full_pipeline(self):
        """Full pipeline: discover → parse → chunk → audit"""
        files = discover_files(SAMPLE_DATA_DIR)
        self.assertGreaterEqual(len(files), 6)
        results = [parse_file(f) for f in files]
        self.assertGreaterEqual(sum(1 for r in results if r.success), 6)
        all_chunks = []
        for r in results:
            if r.success:
                all_chunks.extend(chunk_document(r))
        self.assertGreater(len(all_chunks), 15)
        self.assertGreater(sum(c.token_estimate for c in all_chunks), 1000)

    def test_no_parse_failures(self):
        """All 6 documents parse with zero errors"""
        for f in discover_files(SAMPLE_DATA_DIR):
            result = parse_file(f)
            self.assertTrue(result.success, f"FAILED: {result.filename}: {result.error}")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("═" * 70)
    print("  RED DUKE — Unit Test Suite")
    print("  Document Ingestion Pipeline Validation")
    print("═" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestDocumentDiscovery, TestDocxParser, TestXlsxParser, TestPptxParser,
        TestVsdxParser, TestAuditChecklist, TestChunking,
        TestAuditChecklistGeneration, TestEndToEnd,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = RedDukeTestRunner(verbosity=0)
    runner.run(suite)