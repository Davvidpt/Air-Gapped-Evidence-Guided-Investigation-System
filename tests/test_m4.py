"""Synthetic integration checks for reporting and MVP UI."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from aegis.detection.engine import assess
from aegis.ingestion.importer import ingest
from aegis.reporting.pdf_report import export_pdf, load_snapshot, render_pdf
from scripts.create_assessment_demo import FAKE_RESULTS
from scripts.create_demo_collection import create_zip, SYNTHETIC

ROOT = Path(__file__).resolve().parents[1]
try:
    import reportlab
except ImportError:
    reportlab = None


@unittest.skipUnless(reportlab, 'Install .[mvp] for PDF integration tests')
class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'evidence.db'
        archive = self.root / 'positive.zip'
        create_zip(archive, FAKE_RESULTS)
        self.collection = ingest(archive, self.db)['collection_id']
        self.assessment = assess(self.db, ROOT / 'rules/detection.json', self.collection)

    def test_report_is_readonly_and_findings_have_provenance(self):
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        snapshot = load_snapshot(self.db, self.collection)
        self.assertEqual(snapshot['assessment']['findings_count'], 4)
        for finding in snapshot['assessment']['findings']:
            self.assertTrue(finding['source_member'].startswith('results/'))
            self.assertGreater(finding['source_row'], 0)
        pdf = render_pdf(snapshot, synthetic=True)
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())

    def test_collection_mismatch_and_missing_assessment_rejected(self):
        archive = self.root / 'baseline.zip'
        create_zip(archive, SYNTHETIC)
        second = ingest(archive, self.db)['collection_id']
        with self.assertRaisesRegex(ValueError, 'bukan milik'):
            load_snapshot(self.db, second, self.assessment['assessment_id'])
        with self.assertRaisesRegex(ValueError, 'assessment'):
            load_snapshot(self.db, second)

    def test_output_protection_and_no_database_clobber(self):
        output = self.root / 'report.pdf'
        export_pdf(self.db, self.collection, output)
        original = output.read_bytes()
        with self.assertRaises(FileExistsError):
            export_pdf(self.db, self.collection, output)
        self.assertEqual(original, output.read_bytes())
        with self.assertRaises(ValueError):
            export_pdf(self.db, self.collection, self.db, overwrite=True)
        link = self.root / 'link.pdf'
        link.symlink_to(self.db)
        with self.assertRaises((OSError, ValueError)):
            export_pdf(self.db, self.collection, link, overwrite=True)

    def test_untrusted_markup_and_large_report(self):
        snapshot = load_snapshot(self.db, self.collection)
        finding = snapshot['assessment']['findings'][0]
        finding['observed_value'] = '<img src="https://invalid.example/private"/> & <b>data</b>'
        snapshot['assessment']['findings'] = [dict(finding) for _ in range(60)]
        pdf = render_pdf(snapshot, include_observed=True)
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertGreater(len(pdf), 10000)

    def test_pdf_text_privacy_and_evidence_ids_without_network(self):
        try:
            import pypdfium2 as pdfium
        except ImportError:
            self.skipTest('Install .[verification] for PDF text verification')
        from unittest.mock import patch
        snapshot = load_snapshot(self.db, self.collection)
        for include_observed in (False, True):
            with patch('socket.create_connection', side_effect=AssertionError('Network forbidden')):
                content = render_pdf(snapshot, include_observed=include_observed, synthetic=True)
            with pdfium.PdfDocument(content) as pdf:
                text = '\n'.join(page.get_textpage().get_text_range() for page in pdf)
            self.assertIn('DATA SINTETIS', text)
            for finding in snapshot['assessment']['findings']:
                self.assertIn(finding['rule_id'], text)
                self.assertIn(finding['evidence_id'], text.replace('\r\n', '').replace('\n', ''))
                self.assertEqual(finding['observed_value'] in text, include_observed)

    def test_baseline_pdf_and_missing_db(self):
        archive = self.root / 'baseline.zip'
        create_zip(archive, SYNTHETIC)
        cid = ingest(archive, self.db)['collection_id']
        assess(self.db, ROOT / 'rules/detection.json', cid)
        snapshot = load_snapshot(self.db, cid)
        self.assertEqual(snapshot['assessment']['status'], 'NO_RULE_MATCHES')
        self.assertTrue(render_pdf(snapshot).startswith(b'%PDF-'))
        absent = self.root / 'absent.db'
        with self.assertRaises(FileNotFoundError):
            load_snapshot(absent, 1)
        self.assertFalse(absent.exists())
