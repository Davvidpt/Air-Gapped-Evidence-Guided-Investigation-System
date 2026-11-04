"""Atomic direct ZIP -> SQLite collection importer (M1)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from aegis.coverage.profiles import quick_coverage
from aegis.normalization.normalizer import normalize
from aegis.storage.sqlite import connect
from .parser import artifact_and_query, parse_records
from .validator import CollectionError, validate_zip


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def evidence_id(zip_sha256: str, member: str, row: int) -> str:
    source = f'{zip_sha256}\0{member}\0{row}'.encode('utf-8')
    return hashlib.sha256(source).hexdigest()


def ingest(path: Path, db_path: Path) -> dict:
    path = path.expanduser().resolve(strict=True)
    digest = sha256_file(path)
    db = connect(db_path)
    try:
        existing = db.execute('SELECT id FROM collections WHERE zip_sha256=?', (digest,)).fetchone()
        if existing:
            return summary(db, existing['id'], duplicate=True)

        archive, results = validate_zip(path)
        with archive:
            try:
                with db:  # all-or-nothing: malformed data rolls back imported rows
                    cursor = db.execute('''INSERT INTO collections
                        (zip_sha256, filename, imported_at_utc, status) VALUES (?,?,?,?)''',
                        (digest, path.name, datetime.now(timezone.utc).isoformat(), 'imported'))
                    collection_id = cursor.lastrowid
                    for info in sorted(results, key=lambda i: i.filename):
                        artifact, query = artifact_and_query(info.filename)
                        run = db.execute('''INSERT INTO artifact_runs
                            (collection_id, artifact_name, query_name, zip_member)
                            VALUES (?,?,?,?)''', (collection_id, artifact, query, info.filename))
                        count = 0
                        for row_number, raw in parse_records(archive, info):
                            entity_type, normalized = normalize(artifact, raw)
                            raw_json = json.dumps(raw, ensure_ascii=False, separators=(',', ':'))
                            normalized_json = (json.dumps(normalized, ensure_ascii=False, separators=(',', ':'))
                                               if normalized is not None else None)
                            db.execute('''INSERT INTO evidence
                                (evidence_id, collection_id, artifact_run_id,
                                source_member, source_row, entity_type, raw_json, normalized_json)
                                VALUES (?,?,?,?,?,?,?,?)''',
                                (evidence_id(digest, info.filename, row_number), collection_id,
                                 run.lastrowid, info.filename, row_number, entity_type,
                                 raw_json, normalized_json))
                            count += 1
                        db.execute('UPDATE artifact_runs SET row_count=? WHERE id=?',
                                   (count, run.lastrowid))
            except (UnicodeError, json.JSONDecodeError, sqlite3.DatabaseError, OSError,
                    zipfile.BadZipFile, RuntimeError) as exc:
                raise CollectionError(f'Import gagal; seluruh transaksi dibatalkan: {exc}') from exc
        return summary(db, collection_id)
    finally:
        db.close()


def summary(db: sqlite3.Connection, collection_id: int, duplicate: bool = False) -> dict:
    item = db.execute('SELECT * FROM collections WHERE id=?', (collection_id,)).fetchone()
    if not item:
        raise ValueError('Collection ID tidak ditemukan')
    artifacts = {row['artifact_name']: row['count'] for row in db.execute('''
        SELECT artifact_name,SUM(row_count) AS count FROM artifact_runs
        WHERE collection_id=? GROUP BY artifact_name ORDER BY artifact_name''', (collection_id,))}
    count = db.execute('SELECT COUNT(*) FROM evidence WHERE collection_id=?', (collection_id,)).fetchone()[0]
    assessments = db.execute('SELECT COUNT(*) FROM assessment_runs WHERE collection_id=?', (collection_id,)).fetchone()[0]
    return {
        'assessments': assessments,
        'collection_id': collection_id,
        'filename': item['filename'], 'zip_sha256': item['zip_sha256'],
        'rows': count, 'artifacts': artifacts, 'coverage': quick_coverage(set(artifacts)),
        'duplicate': duplicate,
    }
