"""Deterministic evidence-first M2 assessor; never assigns a malware verdict."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from aegis.coverage.profiles import quick_coverage
from aegis.detection.predicates import PREDICATES
from aegis.mitre.mapper import TECHNIQUES, validate_mapping
from aegis.storage.sqlite import connect

ENGINE_VERSION = 'm2.0.0'
VALID_SEVERITIES = {'low', 'medium', 'high'}
ALLOWED_ARTIFACTS = {
    'autorun_temp_path': 'Windows.Sys.StartupItems',
    'service_temp_path': 'Windows.System.Services',
    'process_temp_path': 'Windows.System.Pslist',
    'powershell_encoded_command': 'Windows.System.Pslist',
}


def load_rules(path: Path) -> tuple[list[dict], str]:
    """Load finite, named rules (no arbitrary expressions or eval)."""
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError(f'Rule pack tidak ditemukan atau terlalu besar: {path}')
    data = path.read_bytes()
    try:
        document = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Rule pack bukan JSON valid: {exc}') from exc
    if not isinstance(document, dict) or document.get('ruleset_version') != 1:
        raise ValueError('Rule pack membutuhkan ruleset_version=1')
    entries = document.get('rules')
    if not isinstance(entries, list) or not (1 <= len(entries) <= 100):
        raise ValueError('Rule pack harus berisi 1–100 rules')
    seen = set()
    enabled = []
    for rule in entries:
        if not isinstance(rule, dict):
            raise ValueError('Setiap rule harus object')
        rid = rule.get('id')
        if not isinstance(rid, str) or not rid.startswith('AEGIS-') or rid in seen:
            raise ValueError(f'Rule ID tidak valid/duplikat: {rid!r}')
        seen.add(rid)
        if not isinstance(rule.get('enabled'), bool):
            raise ValueError(f'Rule {rid} wajib memiliki enabled boolean')
        predicate = rule.get('predicate')
        if predicate not in PREDICATES:
            raise ValueError(f'Rule {rid}: predicate tidak didukung: {predicate!r}')
        if rule.get('artifact') != ALLOWED_ARTIFACTS[predicate]:
            raise ValueError(f'Rule {rid}: artifact tidak sesuai predicate')
        if rule.get('severity') not in VALID_SEVERITIES:
            raise ValueError(f'Rule {rid}: severity tidak valid')
        if not isinstance(rule.get('title'), str) or not rule['title'].strip():
            raise ValueError(f'Rule {rid}: title tidak valid')
        validate_mapping(rule.get('technique_id'), rule.get('tactic'))
        if rule['enabled']:
            enabled.append(rule)
    digest_material = (data + b'\x00' + ENGINE_VERSION.encode() + b'\x00' +
                       json.dumps(TECHNIQUES, sort_keys=True).encode())
    digest = hashlib.sha256(digest_material).hexdigest()
    return enabled, digest


def _ensure_collection(db: sqlite3.Connection, collection_id: int | None) -> int:
    if collection_id is None:
        row = db.execute('SELECT id FROM collections ORDER BY id DESC LIMIT 1').fetchone()
        if row is None:
            raise ValueError('Belum ada collection')
        return row['id']
    row = db.execute('SELECT id FROM collections WHERE id=?', (collection_id,)).fetchone()
    if row is None:
        raise ValueError(f'Collection ID {collection_id} tidak ditemukan')
    return collection_id


def assess(db_path: Path, rules_path: Path, collection_id: int | None = None) -> dict:
    rules, ruleset_sha = load_rules(rules_path)
    if not db_path.is_file():
        raise ValueError(f'Database tidak ditemukan: {db_path}')
    db = connect(db_path)
    try:
        cid = _ensure_collection(db, collection_id)
        previous = db.execute('''SELECT id FROM assessment_runs
            WHERE collection_id=? AND ruleset_sha256=?''', (cid, ruleset_sha)).fetchone()
        if previous:
            return report(db, previous['id'], reused=True)

        by_artifact = defaultdict(list)
        for rule in rules:
            by_artifact[rule['artifact']].append(rule)
        with db:
            run = db.execute('''INSERT INTO assessment_runs
                (collection_id, ruleset_sha256, engine_version, created_at_utc)
                VALUES (?, ?, ?, ?)''',
                (cid, ruleset_sha, ENGINE_VERSION, datetime.now(timezone.utc).isoformat()))
            assessment_id = run.lastrowid
            count = 0
            for ev in db.execute('''SELECT e.evidence_id, e.normalized_json, ar.artifact_name
                FROM evidence e JOIN artifact_runs ar ON ar.id=e.artifact_run_id
                WHERE e.collection_id=? AND e.normalized_json IS NOT NULL
                ORDER BY e.source_member, e.source_row''', (cid,)):
                applicable = by_artifact.get(ev['artifact_name'], ())
                if not applicable:
                    continue
                normalized = json.loads(ev['normalized_json'])
                for rule in applicable:
                    match = PREDICATES[rule['predicate']](normalized)
                    if not match:
                        continue
                    observed, reason = match
                    db.execute('''INSERT INTO findings (
                        assessment_id,evidence_id,rule_id,title,severity,reason,observed_value,
                        technique_id,tactic) VALUES (?,?,?,?,?,?,?,?,?)''',
                        (assessment_id,ev['evidence_id'],rule['id'],rule['title'],rule['severity'],
                         reason,observed,rule.get('technique_id'),rule.get('tactic')))
                    count += 1
            db.execute('UPDATE assessment_runs SET findings_count=? WHERE id=?', (count,assessment_id))
        return report(db, assessment_id)
    finally:
        db.close()


def report(db: sqlite3.Connection, assessment_id: int, reused: bool = False) -> dict:
    run = db.execute('SELECT * FROM assessment_runs WHERE id=?', (assessment_id,)).fetchone()
    if not run:
        raise ValueError(f'Assessment {assessment_id} tidak ditemukan')
    artifact_counts = {r['artifact_name']: r['n'] for r in db.execute('''
        SELECT artifact_name,SUM(row_count) AS n FROM artifact_runs
        WHERE collection_id=? GROUP BY artifact_name''', (run['collection_id'],))}
    findings = [dict(row) for row in db.execute('''SELECT
        id,rule_id,title,severity,reason,observed_value,evidence_id,technique_id,tactic
        FROM findings WHERE assessment_id=? ORDER BY id''',(assessment_id,))]
    grouped = Counter(item['technique_id'] for item in findings if item['technique_id'])
    return {
        'assessment_id': assessment_id,
        'collection_id': run['collection_id'],
        'ruleset_sha256': run['ruleset_sha256'],
        'engine_version': run['engine_version'],
        'status': 'REVIEW_REQUIRED' if findings else 'NO_RULE_MATCHES',
        'disclaimer': 'Tidak ada kecocokan aturan tidak membuktikan endpoint bersih. ATT&CK adalah asosiasi teknik, bukan atribusi atau bukti kompromi.',
        'coverage': quick_coverage(set(artifact_counts)),
        'artifacts': artifact_counts,
        'findings_count': len(findings),
        'techniques': dict(sorted(grouped.items())),
        'findings': findings,
        'reused': reused,
    }
