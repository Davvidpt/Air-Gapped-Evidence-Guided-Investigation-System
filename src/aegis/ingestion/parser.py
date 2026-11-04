"""Read newline-delimited/adjacent JSON records in offline collection result members."""
from __future__ import annotations

import json
from urllib.parse import unquote
from zipfile import ZipFile, ZipInfo

from .validator import CollectionError, MAX_RESULT_MEMBER


def artifact_and_query(member: str) -> tuple[str, str | None]:
    relative = member[len('results/'):].rsplit('.', 1)[0]
    decoded = unquote(relative)
    artifact, separator, query = decoded.partition('/')
    return artifact, (query if separator else None)


def parse_records(archive: ZipFile, info: ZipInfo):
    """Yield (1-based result row, object) from valid JSON/JSONL, never dropping rows."""
    with archive.open(info, 'r') as stream:
        buffer = stream.read(MAX_RESULT_MEMBER + 1)
    if len(buffer) > MAX_RESULT_MEMBER:
        raise CollectionError(f'Ukuran hasil melampaui batas: {info.filename}')
    try:
        text = buffer.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise CollectionError(f'Result bukan UTF-8: {info.filename}') from exc
    decoder = json.JSONDecoder()
    index = row_number = 0
    length = len(text)
    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index == length:
            break
        try:
            value, index = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise CollectionError(f'JSON invalid pada {info.filename}, posisi {exc.pos}') from exc
        values = value if isinstance(value, list) else [value]
        for record in values:
            if not isinstance(record, dict):
                raise CollectionError(f'Baris result bukan JSON object pada {info.filename}')
            row_number += 1
            yield row_number, record
