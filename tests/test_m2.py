"""M2 integration, attribution, schema migration and safety tests, all synthetic."""
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from create_demo_collection import SYNTHETIC, create_zip
from aegis.detection.engine import assess, load_rules
from aegis.coverage.fields import field_audit
from aegis.detection.predicates import PREDICATES
from aegis.ingestion.importer import ingest
from aegis.storage.sqlite import M1_SCHEMA, connect

RULES = ROOT / 'rules' / 'detection.json'


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.db = self.home / 'aegis.db'
        self.zip = self.home / 'input.zip'

    def _collect(self, records):
        create_zip(self.zip, records)
        return ingest(self.zip, self.db)

    def test_benign_baseline_not_flagged(self):
        info = self._collect(SYNTHETIC)
        result = assess(self.db, RULES, info['collection_id'])
        self.assertEqual(result['status'], 'NO_RULE_MATCHES')
        self.assertEqual(result['findings_count'], 0)
        self.assertIn('tidak membuktikan endpoint bersih', result['disclaimer'])
        self.assertEqual(len(result['coverage']['present']), 4)

    def test_synthetic_indicators_findings_and_evidence_trace(self):
        cases = {
            'Windows.Sys.StartupItems': [
                {'Name': 'Synthetic', 'Location': r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run',
                 'Command': r'C:\Users\Lab\AppData\Local\Temp\test-app.exe'}],
            'Windows.System.Services': [
                {'Name': 'LabService', 'PathName': r'"C:\Windows\Temp\LabSvc.exe" -service'}],
            'Windows.System.Pslist': [
                {'Name': 'runner.exe', 'Exe': r'C:\Users\Lab\AppData\Local\Temp\runner.exe'},
                {'Name': 'powershell.exe', 'Exe': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                 'CommandLine': 'powershell.exe -EncodedCommand ZABlAG0AbwA='}
            ]
        }
        source = self._collect(cases)
        result = assess(self.db, RULES, source['collection_id'])
        self.assertEqual(result['findings_count'], 4)
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertEqual(set(result['techniques']), {'T1547.001', 'T1543.003', 'T1059.001'})
        self.assertEqual(len(result['coverage']['missing']), 1)
        with closing(sqlite3.connect(self.db)) as db:
            for finding in result['findings']:
                row = db.execute('SELECT raw_json FROM evidence WHERE evidence_id=?', (finding['evidence_id'],)).fetchone()
                self.assertIsNotNone(row)
                self.assertIsInstance(json.loads(row[0]), dict)

    def test_one_rule_does_not_claim_t1059_from_temp_process(self):
        source = self._collect({'Windows.System.Pslist': [{'Name': 'note.exe', 'Exe': r'C:\Temp\note.exe'}]})
        result = assess(self.db, RULES, source['collection_id'])
        self.assertEqual(result['findings_count'], 1)
        self.assertIsNone(result['findings'][0]['technique_id'])

    def test_false_positive_guard_missing_location_and_unknown_paths(self):
        source = self._collect({'Windows.Sys.StartupItems': [
            {'Name': 'partial', 'Command': r'C:\Users\Test\AppData\Local\Temp\app.exe'},
            {'Name': 'allowed', 'Location': r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run',
             'Command': r'C:\Program Files\Demo\helper.exe'}]})
        result = assess(self.db, RULES, source['collection_id'])
        self.assertEqual(result['findings_count'], 0)

    def test_assessment_idempotent_and_database_persists(self):
        source = self._collect(SYNTHETIC)
        first = assess(self.db, RULES, source['collection_id'])
        second = assess(self.db, RULES, source['collection_id'])
        self.assertFalse(first['reused'])
        self.assertTrue(second['reused'])
        self.assertEqual(first['assessment_id'], second['assessment_id'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM assessment_runs').fetchone()[0], 1)

    def test_rule_id_predicate_allowlist_and_mitre_validation(self):
        original = json.loads(RULES.read_text())
        original['rules'][0]['predicate'] = '__import__'
        file = self.home / 'bad.json'
        file.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, 'predicate'):
            load_rules(file)
        original['rules'][0]['predicate'] = 'autorun_temp_path'
        original['rules'][0]['technique_id'] = 'T9999.999'
        file.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, 'tidak dikenal'):
            load_rules(file)

    def test_field_audit_exposes_missing_normalized_values(self):
        source = self._collect({'Windows.Sys.StartupItems': [
            {'Name': 'one'}, {'Name': 'two', 'Command': r'C:\\Program Files\\App.exe'}]})
        db = connect(self.db)
        try:
            audit = field_audit(db, source['collection_id'])
        finally:
            db.close()
        data = audit['Windows.Sys.StartupItems']
        self.assertEqual(data['rows'], 2)
        self.assertEqual(data['field_nonempty_rows']['name'], 2)
        self.assertEqual(data['field_nonempty_rows']['command'], 1)

    def test_v1_db_migrates_without_losing_evidence(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.executescript(M1_SCHEMA)
            db.execute('PRAGMA user_version=1')
            db.execute('INSERT INTO collections (zip_sha256,filename,imported_at_utc,status) VALUES (?,?,?,?)',
                       ('abc', 'old.zip', '2026-11-03T00:00:00Z', 'imported'))
            db.commit()
        db = connect(self.db)
        try:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT filename FROM collections').fetchone()['filename'], 'old.zip')
            self.assertTrue(db.execute("SELECT 1 FROM sqlite_master WHERE name='findings'").fetchone())
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
