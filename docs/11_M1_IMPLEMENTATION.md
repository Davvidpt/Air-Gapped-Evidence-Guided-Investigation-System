# 11 — Phase 3 / M1 Implementation Record (3 November 2026)

## Delivered

- `python3 -m aegis ingest <ZIP> --db <DB>` standalone, no Velociraptor Server import.
- ZIP structural and CRC validation; no extraction; zipped members treated as untrusted data.
- Raw JSON rows + normalized views for four initial artifacts; preserve unrecognized raw data.
- SQLite v1 schema with `collections`, `artifact_runs`, and `evidence`.
- Stable evidence IDs computed from ZIP SHA-256, ZIP member name and 1-based row index.
- Atomic ingestion and idempotent duplicate handling.
- `summary` shows artifacts, row counts, quick profile coverage and explicitly says assessment was not run.
- Synthetic fixture generator and Python standard-library test suite.

## Known constraints / TODO

1. Validate actual field keys and member layout against a benign Velociraptor v0.77.3 collector ZIP; adapters currently accept common, conservative aliases but not all potential version-specific shapes.
2. No support for encrypted double-ZIP collectors; only non-sensitive lab data until secure production handling is designed.
3. No detection, MITRE scoring, LLM or dashboard implemented in M1.
4. The 350 MiB uncompressed limit and 64 MiB member limit exclude large EVTX/full forensic collections; streaming parser is a later improvement.
5. M1 rejects the entire import if any result JSON is malformed; later versions may retain partial evidence with explicit completeness records.
6. Hostname and original collector timestamps remain null unless they can be proven from source metadata; filename is not treated as authenticated identity.
7. Raw ZIP stays where placed; database preserves rows, but user must maintain separate custody of original ZIP.
8. An unencrypted SQLite file is not an appropriate unprotected store for sensitive/organizational evidence.

## Acceptance commands

```bash
python3 scripts/create_demo_collection.py data/incoming/demo-collection.zip
PYTHONPATH=src python3 -m aegis ingest data/incoming/demo-collection.zip --db data/aegis-v1.db
PYTHONPATH=src python3 -m aegis summary --db data/aegis-v1.db
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

M1 closes only when the synthetic integration tests pass AND the user confirms ingest of one genuine, permissioned lab ZIP from the same collector version.
