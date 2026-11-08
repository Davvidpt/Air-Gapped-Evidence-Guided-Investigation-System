"""AEGIS CLI — ingestion (M1) and assessment (M2)."""
from __future__ import annotations

import argparse
import json
import sys
import sqlite3
from pathlib import Path

from aegis.detection.engine import assess
from aegis.coverage.fields import field_audit
from aegis.ingestion.importer import ingest, summary
from aegis.ingestion.validator import CollectionError
from aegis.storage.sqlite import connect


def print_summary(info: dict):
    print('Status          :', 'DUPLICATE / already imported' if info['duplicate'] else 'IMPORTED')
    print('Collection ID   :', info['collection_id'])
    print('ZIP             :', info['filename'])
    print('ZIP SHA-256     :', info['zip_sha256'])
    print('Evidence rows   :', info['rows'])
    print('Artifact breakdown:')
    for name, count in sorted(info['artifacts'].items()):
        print(f'  {name}: {count}')
    cv = info['coverage']
    print(f"Quick profile   : {len(cv['present'])}/{cv['required']} artifacts present")
    if cv['missing']:
        print('Missing         :', ', '.join(cv['missing']))
    print('Assessments     :', info.get('assessments', 0))
    print('NOTE            : Coverage is artifact availability, not security assurance.')


def print_assessment(info: dict):
    print('Assessment ID   :', info['assessment_id'])
    print('Collection ID   :', info['collection_id'])
    print('Status          :', info['status'])
    print('Findings        :', info['findings_count'])
    print('Assessment      :', 'REUSED (unchanged rules)' if info['reused'] else 'CREATED')
    cv = info['coverage']
    print(f"Quick coverage  : {len(cv['present'])}/{cv['required']} artifact types available")
    for tech, count in info['techniques'].items():
        print(f'  MITRE related : {tech} ({count} findings)')
    for finding in info['findings'][:25]:
        mitre = finding['technique_id'] or 'unmapped'
        print(f"  [{finding['severity'].upper()}] {finding['rule_id']} / {mitre}"
              f" / evidence {finding['evidence_id'][:12]}…")
    if len(info['findings']) > 25:
        print(f"  ... plus {len(info['findings']) - 25} further findings (use --json)")
    print('WARNING         : No findings does NOT mean endpoint is clean.')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='AEGIS offline evidence ingestion & assessment')
    command = parser.add_subparsers(dest='command', required=True)
    imp = command.add_parser('ingest', help='Import unencrypted Velociraptor ZIP')
    imp.add_argument('collection_zip', type=Path)
    imp.add_argument('--db', default='data/aegis-v1.db', type=Path)
    view = command.add_parser('summary', help='Show evidence counts and quick profile coverage')
    view.add_argument('--db', default='data/aegis-v1.db', type=Path)
    view.add_argument('--collection', type=int, help='Collection ID (default latest)')
    view.add_argument('--json', action='store_true')
    analyze = command.add_parser('assess', help='Evaluate deterministic rules, persist findings with evidence IDs')
    analyze.add_argument('--db', default='data/aegis-v1.db', type=Path)
    analyze.add_argument('--collection', type=int, help='Collection ID (default latest)')
    analyze.add_argument('--rules', default='rules/detection.json', type=Path)
    analyze.add_argument('--json', action='store_true', help='Print findings including observed values; protect output')
    diag = command.add_parser('inspect-fields', help='Audit normalized field availability without printing private values')
    diag.add_argument('--db', default='data/aegis-v1.db', type=Path)
    diag.add_argument('--collection', type=int, help='Collection ID (default latest)')
    diag.add_argument('--json', action='store_true')
    pdf = command.add_parser('report', help='Export persisted assessment to Indonesian PDF')
    pdf.add_argument('--db', default='data/aegis-v1.db', type=Path)
    pdf.add_argument('--collection', required=True, type=int)
    pdf.add_argument('--assessment', type=int, help='Default: latest assessment for collection')
    pdf.add_argument('--out', required=True, type=Path)
    pdf.add_argument('--overwrite', action='store_true')
    pdf.add_argument('--include-observed', action='store_true', help='Include sensitive observed values')
    pdf.add_argument('--synthetic', action='store_true', help='Label report as synthetic demonstration')
    args = parser.parse_args(argv)
    try:
        if args.command == 'report':
            from aegis.reporting.pdf_report import export_pdf
            output = export_pdf(args.db, args.collection, args.out, args.assessment,
                                args.overwrite, args.include_observed, args.synthetic)
            print(f'PDF dibuat: {output}')
            return 0
        if args.command == 'ingest':
            data = ingest(args.collection_zip, args.db)
        elif args.command == 'assess':
            data = assess(args.db, args.rules, args.collection)
        else:
            if not args.db.is_file():
                raise ValueError(f'Database tidak ditemukan: {args.db}')
            db = connect(args.db)
            try:
                collection = args.collection
                if collection is None:
                    row = db.execute('SELECT id FROM collections ORDER BY id DESC LIMIT 1').fetchone()
                    if row is None:
                        raise ValueError('Belum ada collection di database')
                    collection = row['id']
                data = field_audit(db, collection) if args.command == 'inspect-fields' else summary(db, collection)
            finally:
                db.close()
        if getattr(args, 'json', False):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif args.command == 'assess':
            print_assessment(data)
        elif args.command == 'inspect-fields':
            for artifact, audit in data.items():
                print(f"{artifact}: {audit['rows_with_any_normalized_value']}/{audit['rows']} rows with values")
                for name, count in audit['field_nonempty_rows'].items():
                    print(f'  {name}: {count}/{audit["rows"]}')
            print('NOTE: This is field availability only, not detection coverage.')
        else:
            print_summary(data)
        return 0
    except (OSError, ValueError, CollectionError, RuntimeError, sqlite3.Error) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
