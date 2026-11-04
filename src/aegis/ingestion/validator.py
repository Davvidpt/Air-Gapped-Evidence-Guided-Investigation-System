"""Bounded, non-extracting validation of Velociraptor collection ZIPs."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import List

MAX_FILES = 2_000
MAX_UNCOMPRESSED = 350 * 1024 * 1024
MAX_RESULT_MEMBER = 64 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000


class CollectionError(ValueError):
    """Input is unsupported or unsafe for this MVP parser."""


def _safe_member_name(name: str) -> bool:
    # Do not extract, but still reject confusing/unsafe names up front.
    if not name or '\x00' in name or '\\' in name:
        return False
    if name.startswith('/') or re.match(r'^[A-Za-z]:', name):
        return False
    segments = name.rstrip('/').split('/')
    if any(segment in ('', '.', '..') for segment in segments):
        return False
    return True


def validate_zip(path: Path) -> tuple[zipfile.ZipFile, List[zipfile.ZipInfo]]:
    """Return an open ZIP and result members after checks. Caller MUST close it."""
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise CollectionError('Bukan file ZIP collection yang valid')
    archive = zipfile.ZipFile(path, 'r')
    try:
        members = archive.infolist()
        if len(members) > MAX_FILES:
            raise CollectionError(f'Terlalu banyak entri ZIP (maksimum {MAX_FILES})')
        names: set[str] = set()
        total = 0
        selected: List[zipfile.ZipInfo] = []
        for info in members:
            name = info.filename
            if not _safe_member_name(name):
                raise CollectionError(f'Path tidak aman dalam ZIP: {name!r}')
            if name in names:
                raise CollectionError(f'Nama entri ZIP duplikat: {name!r}')
            names.add(name)
            if info.flag_bits & 0x1:
                raise CollectionError('ZIP terenkripsi tidak didukung versi MVP ini')
            total += info.file_size
            if total > MAX_UNCOMPRESSED:
                raise CollectionError('Total ukuran dekompresi melebihi batas MVP (350 MiB)')
            if info.file_size and info.file_size / max(1, info.compress_size) > MAX_COMPRESSION_RATIO:
                raise CollectionError(f'Rasio kompresi tidak wajar: {name!r}')
            if not info.is_dir() and name.startswith('results/') and name.lower().endswith(('.json', '.jsonl')):
                if info.file_size > MAX_RESULT_MEMBER:
                    raise CollectionError(f'Result member terlalu besar (maks 64 MiB): {name!r}')
                selected.append(info)

        if {'data.zip', 'metadata.json'}.issubset(names):
            raise CollectionError('Collection encrypted/double ZIP: dekripsi dahulu di stasiun tepercaya')
        if not selected:
            raise CollectionError('Tidak ada results/*.json atau *.jsonl dalam ZIP')
        # CRC check for *all* ZIP members. We never extract files to disk.
        try:
            broken = archive.testzip()
        except (RuntimeError, OSError, NotImplementedError, ValueError, EOFError) as exc:
            raise CollectionError(f'ZIP gagal dibaca: {exc}') from exc
        if broken:
            raise CollectionError(f'CRC ZIP tidak cocok pada: {broken!r}')
        return archive, selected
    except Exception:
        archive.close()
        raise
