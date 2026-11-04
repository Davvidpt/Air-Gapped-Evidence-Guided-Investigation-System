"""Field-level audit: how many normalized values are actually usable per artifact.

Does NOT measure whether a host is clean or threats are covered.
"""
from __future__ import annotations
import json
import sqlite3
from collections import defaultdict, Counter


def field_audit(db: sqlite3.Connection, collection_id: int) -> dict:
    totals = Counter()
    nonempty = Counter()
    fields = defaultdict(Counter)
    for row in db.execute('''SELECT ar.artifact_name,e.normalized_json
        FROM evidence e JOIN artifact_runs ar ON ar.id=e.artifact_run_id
        WHERE e.collection_id=?''', (collection_id,)):
        name = row['artifact_name']
        totals[name] += 1
        if row['normalized_json'] is None:
            continue
        values = json.loads(row['normalized_json'])
        if not isinstance(values, dict):
            continue
        present = False
        for field, value in values.items():
            if value is not None and value != '' and value != [] and value != {}:
                fields[name][field] += 1
                present = True
        if present:
            nonempty[name] += 1
    return {name: {
        'rows': totals[name],
        'rows_with_any_normalized_value': nonempty[name],
        'field_nonempty_rows': dict(sorted(fields[name].items())),
    } for name in sorted(totals)}
