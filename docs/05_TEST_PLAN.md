# 05 — Verification and evaluation plan

## Test fixtures

- Synthetic four-artifact ZIP with a documented row count and expected fields.
- Incomplete ZIP missing a required artifact.
- ZIP with corrupt JSON member and another valid member (M1: atomic rejection, not partial import).
- ZIP with unsafe path entries, duplicates, oversized member, corrupt CRC.
- Duplicate import of an unchanged ZIP.
- Benign baseline Windows VM + controlled, authorized test changes (e.g., test autorun entry, service metadata, scheduled task).
- Optional several synthetic host identities with a shared indicator for correlation.

## Unit tests

`zip_validator`: malformed files/quota/path/CRC; `json_parser`: JSONL and JSON objects; `normalizers`: unknown/missing fields; `rules`: positive, negative, false-positive examples; `mitre`: allowed/nonexistent IDs; `coverage`: missing vs not detected; `ai`: reject fabricated evidence IDs.

## Integration test

`ZIP -> SQLite -> Rule Findings -> ATT&CK mappings -> HTML report` in one deterministic offline command. Verify every finding ID resolves to real source member/row and no additional raw bytes are silently lost.

## E2E/demo tests

1. Import synthetic ZIP into fresh database; count expected rows; produce report.
2. Import same ZIP again: zero additional evidence rows.
3. Import incomplete ZIP: partial coverage, never status clean.
4. Import different synthetic endpoint: show separate host and optional shared indicator.
5. Disable Ollama: repeat E2E and produce same deterministic findings.
6. Offline test: with network disconnected, analysis and reports still operate.

## Metrics to record

- ZIP size / import duration / peak memory if available.
- Rows parsed, skipped and rejected with reasons.
- Expected findings matched, missed findings and false alarms on known ground-truth fixtures.
- Per-profile artifact coverage (NOT effectiveness of detecting unknown attacks).
- Model explanation citation validity and unsupported claim rate on scripted test questions.

Do not claim real-world detection rate from a handful of controlled tests.
