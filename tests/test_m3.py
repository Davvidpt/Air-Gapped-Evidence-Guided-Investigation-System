"""M3 dashboard query tests; no Streamlit installation required."""
import tempfile
import unittest
from pathlib import Path

from aegis.detection.engine import assess
from aegis.ingestion.importer import ingest
from aegis.ui import store
from scripts.create_assessment_demo import FAKE_RESULTS
from scripts.create_demo_collection import create_zip


class DashboardReadTests(unittest.TestCase):
    def test_readonly_backend_and_evidence_trace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            zip_path = root / 'demo.zip'
            create_zip(zip_path, FAKE_RESULTS)
            db_path = root / 'aegis.db'
            collection = ingest(zip_path, db_path)
            project_root = Path(__file__).resolve().parents[1]
            result = assess(db_path, project_root / 'rules/detection.json', collection['collection_id'])
            self.assertTrue(store.collections(db_path))
            self.assertEqual(store.collections(db_path)[0]['evidence_count'], collection['rows'])
            self.assertTrue(store.artifacts(db_path, collection['collection_id']))
            self.assertEqual(store.assessments(db_path, collection['collection_id'])[0]['id'], result['assessment_id'])
            entries = store.findings(db_path, result['assessment_id'])
            self.assertTrue(entries)
            item = store.evidence(db_path, entries[0]['evidence_id'], collection['collection_id'])
            self.assertIsInstance(item['raw_json'], dict)
            self.assertIn('source_member', item)
            self.assertIsNone(store.evidence(db_path, 'not-an-id', collection['collection_id']))
            self.assertIn('required', store.profile_coverage(db_path, collection['collection_id']))
            self.assertTrue(store.normalized_field_audit(db_path, collection['collection_id']))

    def test_nonexistent_database_fails_without_creation(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'missing.db'
            with self.assertRaises(FileNotFoundError):
                store.collections(p)
            self.assertFalse(p.exists())

if __name__ == '__main__':
    unittest.main()
