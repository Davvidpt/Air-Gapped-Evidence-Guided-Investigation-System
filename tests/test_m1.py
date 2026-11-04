import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from aegis.ingestion.importer import ingest, sha256_file
from aegis.ingestion.validator import CollectionError
from aegis.coverage.profiles import quick_coverage
from create_demo_collection import create_zip, SYNTHETIC


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.zip = self.base / 'Collection-LAB.zip'
        self.db = self.base / 'aegis.db'

    def test_complete_collection_and_provenance(self):
        create_zip(self.zip)
        result = ingest(self.zip, self.db)
        self.assertEqual(result['rows'], 5)
        self.assertEqual(len(result['artifacts']), 4)
        self.assertEqual(len(result['coverage']['missing']), 0)
        self.assertEqual(result['zip_sha256'], sha256_file(self.zip))
        with closing(sqlite3.connect(self.db)) as db:
            row = db.execute('SELECT evidence_id,raw_json,normalized_json FROM evidence LIMIT 1').fetchone()
        self.assertEqual(len(row[0]), 64)
        self.assertTrue(isinstance(json.loads(row[1]), dict))
        self.assertTrue(isinstance(json.loads(row[2]), dict))

    def test_duplicate_does_not_increase_rows(self):
        create_zip(self.zip)
        first = ingest(self.zip, self.db)
        second = ingest(self.zip, self.db)
        self.assertEqual(first['collection_id'], second['collection_id'])
        self.assertTrue(second['duplicate'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0], 5)

    def test_missing_artifact_not_interpreted_as_clean(self):
        create_zip(self.zip, {'Windows.System.Pslist': SYNTHETIC['Windows.System.Pslist']})
        result = ingest(self.zip, self.db)
        self.assertEqual(result['rows'], 2)
        self.assertEqual(len(result['coverage']['missing']), 3)

    def test_unknown_artifact_preserved_raw(self):
        create_zip(self.zip, {'Custom.Test.Artifact': [{'Unrecognized': 123}]})
        result = ingest(self.zip, self.db)
        self.assertEqual(result['rows'], 1)
        with closing(sqlite3.connect(self.db)) as db:
            row = db.execute('SELECT entity_type, normalized_json, raw_json FROM evidence').fetchone()
        self.assertIsNone(row[0])
        self.assertIsNone(row[1])
        self.assertEqual(json.loads(row[2])['Unrecognized'], 123)

    def test_corrupt_json_rolls_back_collection(self):
        with zipfile.ZipFile(self.zip, 'w') as archive:
            archive.writestr('results/Windows.System.Pslist.json', '{"Name":"ok"}\nINVALID')
        with self.assertRaises(CollectionError):
            ingest(self.zip, self.db)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM collections').fetchone()[0], 0)

    def test_path_traversal_rejected(self):
        with zipfile.ZipFile(self.zip, 'w') as archive:
            archive.writestr('../unsafe.txt', 'test')
            archive.writestr('results/Windows.System.Pslist.json', '{"Name":"ok"}\n')
        with self.assertRaisesRegex(CollectionError, 'tidak aman'):
            ingest(self.zip, self.db)

    def test_duplicate_zip_member_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.zip, 'w') as archive:
                archive.writestr('results/Windows.System.Pslist.json', '{}\n')
                archive.writestr('results/Windows.System.Pslist.json', '{}\n')
        with self.assertRaisesRegex(CollectionError, 'duplikat'):
            ingest(self.zip, self.db)

    def test_json_array_and_concatenated_objects(self):
        with zipfile.ZipFile(self.zip, 'w') as archive:
            archive.writestr('results/Windows.System.Pslist.json',
                             '[{"Name":"a"},{"Name":"b"}]\n{"Name":"c"}')
        result = ingest(self.zip, self.db)
        self.assertEqual(result['rows'], 3)

    def test_normalized_values_are_not_invented(self):
        create_zip(self.zip, {'Windows.System.Pslist': [{'Name': 'only-name.exe'}]})
        ingest(self.zip, self.db)
        with closing(sqlite3.connect(self.db)) as db:
            record = json.loads(db.execute('SELECT normalized_json FROM evidence').fetchone()[0])
        self.assertEqual(record['name'], 'only-name.exe')
        self.assertIsNone(record['pid'])
        self.assertIsNone(record['command_line'])

    def test_filename_decodes_velociraptor_query_suffix(self):
        create_zip(self.zip)
        ingest(self.zip, self.db)
        with closing(sqlite3.connect(self.db)) as db:
            row = db.execute('SELECT artifact_name, query_name FROM artifact_runs '
                             'WHERE artifact_name=?', ('Windows.System.Pslist',)).fetchone()
        self.assertEqual(row, ('Windows.System.Pslist', 'Query'))

    def test_oversize_uncompressed_rejected(self):
        # Avoid large files in tests; import validator constants patch instead.
        from unittest.mock import patch
        import aegis.ingestion.validator as validator
        create_zip(self.zip)
        with patch.object(validator, 'MAX_UNCOMPRESSED', 1):
            with self.assertRaisesRegex(CollectionError, 'melebihi batas'):
                ingest(self.zip, self.db)


if __name__ == '__main__':
    unittest.main()
