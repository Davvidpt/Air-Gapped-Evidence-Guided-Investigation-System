#!/usr/bin/env python3
"""AEGIS MVP ZIP importer for Velociraptor unencrypted offline collections.

Accepts JSON/JSONL data under results/ only. No archive extraction, no executing data.
Records source ZIP hash, member, row number, and full raw object in SQLite.
Does not perform malware detection or prove evidence authenticity.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

MAX_ENTRIES = 2000
MAX_TOTAL_UNCOMPRESSED = 350 * 1024 * 1024
MAX_RESULT_MEMBER = 64 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def parse_objects(text: str):
    """Parse JSONL, an array of objects, or adjacent JSON objects."""
    decoder = json.JSONDecoder()
    cursor = 0
    n = len(text)
    while cursor < n:
        while cursor < n and text[cursor].isspace():
            cursor += 1
        if cursor >= n:
            break
        value, cursor = decoder.raw_decode(text, cursor)
        if isinstance(value, dict):
            yield value
        elif isinstance(value, list):
            for row in value:
                if isinstance(row, dict):
                    yield row
                else:
                    raise ValueError('JSON list contains a non-object row')
        else:
            raise ValueError('JSON result is not an object or array')


def init_db(db: sqlite3.Connection):
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY,
        filename TEXT NOT NULL,
        zip_sha256 TEXT NOT NULL UNIQUE,
        imported_utc TEXT NOT NULL,
        status TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY,
        collection_id INTEGER NOT NULL REFERENCES collections(id),
        artifact TEXT NOT NULL,
        member TEXT NOT NULL,
        row_number INTEGER NOT NULL,
        raw_json TEXT NOT NULL,
        UNIQUE(collection_id, member, row_number)
    );
    CREATE INDEX IF NOT EXISTS idx_evidence_artifact ON evidence(artifact);
    ''')


def run(zip_path: Path, db_path: Path):
    if not zip_path.is_file() or not zipfile.is_zipfile(zip_path):
        raise ValueError('Input bukan arsip ZIP yang valid')
    digest = sha256(zip_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    try:
        init_db(db)
        if db.execute('SELECT 1 FROM collections WHERE zip_sha256=?', (digest,)).fetchone():
            print('ZIP ini sudah pernah diimpor (hash sama), tidak ada duplikasi.')
            return

        with zipfile.ZipFile(zip_path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES:
                raise ValueError('Terlalu banyak entri dalam ZIP')
            if sum(e.file_size for e in entries) > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError('Ukuran ZIP setelah dekompresi melebihi batas MVP')
            targets = [e for e in entries if
                       e.filename.lstrip('/').startswith('results/')
                       and e.filename.lower().endswith(('.json', '.jsonl'))
                       and not e.is_dir()]
            if not targets:
                raise ValueError('Tidak ditemukan results/*.json; cek format/enkripsi ZIP')

            rows_total, counts = 0, {}
            with db:
                cursor = db.execute(
                    'INSERT INTO collections (filename, zip_sha256, imported_utc, status) VALUES (?,?,?,?)',
                    (zip_path.name, digest, datetime.now(timezone.utc).isoformat(), 'importing'))
                collection_id = cursor.lastrowid
                for e in targets:
                    if e.file_size > MAX_RESULT_MEMBER:
                        raise ValueError(f'File hasil terlalu besar: {e.filename}')
                    # zipfile transparently validates CRC when read completely.
                    with archive.open(e) as stream:
                        raw = stream.read(MAX_RESULT_MEMBER + 1)
                    if len(raw) > MAX_RESULT_MEMBER:
                        raise ValueError(f'File melebihi batas: {e.filename}')
                    text = raw.decode('utf-8-sig')
                    artifact = e.filename.lstrip('/')[len('results/'):].rsplit('.', 1)[0]
                    artifact = artifact.replace('%2F', '/').replace('%2f', '/')
                    for number, record in enumerate(parse_objects(text), 1):
                        db.execute(
                            'INSERT INTO evidence(collection_id,artifact,member,row_number,raw_json) VALUES (?,?,?,?,?)',
                            (collection_id, artifact, e.filename, number,
                             json.dumps(record, ensure_ascii=False, separators=(',', ':'))))
                        rows_total += 1
                        counts[artifact] = counts.get(artifact, 0) + 1
                db.execute('UPDATE collections SET status=? WHERE id=?', ('imported', collection_id))

            print(f'Berhasil import: {zip_path.name}')
            print(f'SHA-256 ZIP     : {digest}')
            print(f'SQLite         : {db_path}')
            print(f'Total evidence : {rows_total} baris')
            for name, count in sorted(counts.items()):
                print(f'  {name}: {count}')
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AEGIS: importer ZIP Velociraptor (lab, tanpa enkripsi)')
    parser.add_argument('collection_zip', type=Path)
    parser.add_argument('--db', type=Path, default=Path('data/aegis.db'))
    args = parser.parse_args()
    try:
        run(args.collection_zip, args.db)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile, RuntimeError) as exc:
        print(f'Gagal import: {exc}', file=sys.stderr)
        sys.exit(1)
