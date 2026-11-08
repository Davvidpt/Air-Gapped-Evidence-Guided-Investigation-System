#!/usr/bin/env python3
"""Reproducible synthetic MVP demo; never opens an existing evidence database."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from create_demo_collection import SYNTHETIC, create_zip
from create_assessment_demo import FAKE_RESULTS
from aegis.ingestion.importer import ingest
from aegis.detection.engine import assess
from aegis.reporting.pdf_report import export_pdf


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    results = {'synthetic': True, 'cases': {}}
    for name, records, expected in [('baseline', SYNTHETIC, 0), ('positive', FAKE_RESULTS, 4)]:
        archive = create_zip(output / f'{name}.zip', records)
        database = output / f'{name}.db'
        started = perf_counter()
        collection = ingest(archive, database)
        ingested = perf_counter()
        assessment = assess(database, ROOT / 'rules/detection.json', collection['collection_id'])
        assessed = perf_counter()
        assert assessment['findings_count'] == expected
        if name == 'positive':
            assert set(assessment['techniques']) == {'T1547.001', 'T1543.003', 'T1059.001'}
        export_pdf(database, collection['collection_id'], output / f'{name}.pdf', synthetic=True)
        finished = perf_counter()
        assert ingest(archive, database)['duplicate']
        assert assess(database, ROOT / 'rules/detection.json', collection['collection_id'])['reused']
        results['cases'][name] = {
            'rows': collection['rows'], 'findings': assessment['findings_count'],
            'status': assessment['status'], 'techniques': assessment['techniques'],
            'seconds': {'ingest': round(ingested-started, 4),
                        'assess': round(assessed-ingested, 4), 'pdf': round(finished-assessed, 4)},
            'idempotence': 'passed',
        }
    (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'reports/generated' /
                        ('mvp-demo-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    args = parser.parse_args()
    print(json.dumps(run(args.out), indent=2))
    print(f'Artifacts: {args.out}')
