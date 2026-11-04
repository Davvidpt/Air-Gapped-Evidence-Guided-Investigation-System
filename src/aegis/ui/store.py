"""Read-only, parameterized SQL queries for the AEGIS M3 local dashboard.

No database schema change. Display-only logic never changes the security assessment.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.parse import quote


def _read_db(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path).expanduser().resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f'Database tidak ditemukan: {db_path}')
    # Open in SQLite read-only mode; dashboard reads never create a new database.
    uri = 'file:' + quote(str(db_path), safe='/') + '?mode=ro'
    db = sqlite3.connect(uri, uri=True, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def collections(db_path: Path) -> list[dict]:
    db = _read_db(db_path)
    try:
        return [dict(x) for x in db.execute('''
            SELECT c.id, c.filename, c.zip_sha256, c.imported_at_utc,
                c.host_name, c.status, COUNT(e.evidence_id) AS evidence_count
            FROM collections c LEFT JOIN evidence e ON e.collection_id=c.id
            GROUP BY c.id ORDER BY c.id DESC''')]
    finally:
        db.close()


def assessments(db_path: Path, collection_id: int) -> list[dict]:
    db = _read_db(db_path)
    try:
        return [dict(x) for x in db.execute('''
            SELECT id, collection_id, engine_version, ruleset_sha256,
                created_at_utc, findings_count FROM assessment_runs
            WHERE collection_id=? ORDER BY id DESC''', (collection_id,))]
    finally:
        db.close()


def artifacts(db_path: Path, collection_id: int) -> list[dict]:
    db = _read_db(db_path)
    try:
        return [dict(x) for x in db.execute('''
            SELECT artifact_name, SUM(row_count) AS row_count, COUNT(*) AS files
            FROM artifact_runs WHERE collection_id=?
            GROUP BY artifact_name ORDER BY artifact_name''', (collection_id,))]
    finally:
        db.close()


def findings(db_path: Path, assessment_id: int) -> list[dict]:
    db = _read_db(db_path)
    try:
        return [dict(x) for x in db.execute('''
            SELECT f.id, f.rule_id, f.title, f.severity, f.reason, f.observed_value,
                f.evidence_id, f.technique_id, f.tactic, e.source_member, e.source_row,
                e.entity_type
            FROM findings f JOIN evidence e ON e.evidence_id=f.evidence_id
            WHERE f.assessment_id=? ORDER BY
                CASE f.severity WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                f.id''', (assessment_id,))]
    finally:
        db.close()


def evidence(db_path: Path, evidence_id: str, collection_id: int) -> dict | None:
    db = _read_db(db_path)
    try:
        row = db.execute('''
            SELECT evidence_id, source_member, source_row, entity_type,
                raw_json, normalized_json, event_time_utc
            FROM evidence WHERE evidence_id=? AND collection_id=?''',
            (evidence_id, collection_id)).fetchone()
        if row is None:
            return None
        item = dict(row)
        for key in ('raw_json', 'normalized_json'):
            try:
                item[key] = json.loads(item[key]) if item[key] is not None else None
            except json.JSONDecodeError:
                item[key] = {'error': 'JSON tidak valid pada data tersimpan'}
        return item
    finally:
        db.close()


def profile_coverage(db_path: Path, collection_id: int) -> dict:
    from aegis.coverage.profiles import quick_coverage
    names = {r['artifact_name'] for r in artifacts(db_path, collection_id)}
    return quick_coverage(names)


def normalized_field_audit(db_path: Path, collection_id: int) -> dict:
    from aegis.coverage.fields import field_audit
    db = _read_db(db_path)
    try:
        return field_audit(db, collection_id)
    finally:
        db.close()
