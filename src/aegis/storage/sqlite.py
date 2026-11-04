"""SQLite schema v2; upgrade v1 in place without losing imported evidence."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 2

M1_SCHEMA = '''
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY,
    zip_sha256 TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    imported_at_utc TEXT NOT NULL,
    host_name TEXT,
    profile TEXT NOT NULL DEFAULT 'quick',
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artifact_runs (
    id INTEGER PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    artifact_name TEXT NOT NULL,
    query_name TEXT,
    zip_member TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    parse_status TEXT NOT NULL DEFAULT 'ok',
    UNIQUE (collection_id,zip_member)
);
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    artifact_run_id INTEGER NOT NULL REFERENCES artifact_runs(id) ON DELETE CASCADE,
    source_member TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    event_time_utc TEXT,
    entity_type TEXT,
    raw_json TEXT NOT NULL,
    normalized_json TEXT,
    UNIQUE(collection_id,source_member,source_row)
);
CREATE INDEX IF NOT EXISTS idx_evidence_collection ON evidence(collection_id);
CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence(entity_type);
CREATE INDEX IF NOT EXISTS idx_artifact_runs_collection ON artifact_runs(collection_id);
'''

M2_SCHEMA = '''
CREATE TABLE IF NOT EXISTS assessment_runs (
    id INTEGER PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    ruleset_sha256 TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    findings_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(collection_id, ruleset_sha256)
);
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessment_runs(id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL,
    observed_value TEXT,
    technique_id TEXT,
    tactic TEXT,
    UNIQUE(assessment_id, rule_id, evidence_id)
);
CREATE INDEX IF NOT EXISTS idx_findings_assessment ON findings(assessment_id);
CREATE INDEX IF NOT EXISTS idx_findings_technique ON findings(technique_id);
'''


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version not in (0, 1, SCHEMA_VERSION):
        db.close()
        raise ValueError(f'Schema SQLite versi {version} tidak didukung')
    if version == 0 and db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='collections'").fetchone():
        db.close()
        raise ValueError('Database memakai schema prototype lama, tidak dapat dimigrasikan otomatis')
    if version == 0:
        db.executescript(M1_SCHEMA)
        db.execute('PRAGMA user_version=1')
        db.commit()
    if version in (0, 1):
        # Existing v1 data is untouched; only additive tables and indexes.
        db.executescript(M2_SCHEMA)
        db.execute('PRAGMA user_version=2')
        db.commit()
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return db
