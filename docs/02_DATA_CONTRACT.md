# 02 — Data contracts and provenance

## Principles

- Raw data is immutable within the logical evidence store; all normalized fields refer to the raw source.
- Every finding must cite >=1 actual evidence row; unknown/missing fields are NULL, never guessed.
- UTC for normalized instants, preserving source timestamp text and timezone uncertainty.
- `Collection.zip` SHA-256 is an identity/fixity check. A hash computed after receipt **does not establish authenticity**. Verification against a trusted, independently recorded source is a separate step.
- Artifact member names may contain `%2F` which divides artifact and query names. Never assume all files are plain `.jsonl`.

## SQLite schema v1 (implemented in M1 for the three core tables)

### collections
`id`, `zip_sha256` (unique), `filename`, `imported_at_utc`, `host_name` nullable, `profile`, `status`. Collection timestamp, collector version, and warnings are future fields.

### artifact_runs
`id`, `collection_id` FK, `artifact_name`, `query_name` nullable, `zip_member`, `row_count`, `parse_status` (currently only `ok`). Failure rolls back the whole import in M1.

### evidence
`evidence_id` (stable), `collection_id`, `artifact_run_id`, `source_member`, `source_row` (1-based), `event_time_utc` nullable (unset in M1), `entity_type` nullable, `raw_json`, `normalized_json` nullable.

`evidence_id = SHA256(zip_sha256 + NUL + source_member + NUL + row_index)` (defined once in code; JSON path is an untrusted string and never evaluated).

### assessment_runs (implemented M2, schema v2)
`id`, `collection_id` FK, `ruleset_sha256`, `engine_version`, `created_at_utc`, `findings_count`. Unique `(collection_id, ruleset_sha256)` supports assessment reuse.

### findings (implemented M2)
`id`, `assessment_id` FK, `evidence_id` FK, `rule_id`, `title`, `severity`, `reason`, `observed_value`, `technique_id` nullable, `tactic` nullable. Unique `(assessment_id, rule_id, evidence_id)`. Each finding currently references one evidence row. Many-to-many evidence links and a separate technique mapping table remain future designs.

M3 dashboard and M4 reporting read this schema; no new tables are required. M4 reports select a persisted assessment, check collection ownership and include source member/row references.

### ai_notes (planned, not implemented)
`finding_id` nullable, `model_id`, `prompt_version`, `generated_text`, `validated_evidence_ids_json`, `generation_status`.

## Normalization targets (first adapters)

| Artifact | Useful fields | Entity type |
|---|---|---|
| Windows.System.Pslist | name, pid, ppid, path, command line if present | process |
| Windows.Network.Netstat | local/remote addresses, port, protocol, state, owning PID if present | connection |
| Windows.System.Services | service name, image path, start mode, state | service |
| Windows.Sys.StartupItems | entry name, location, command, state | autorun |

Unknown keys stay in `raw_json`. Do not fabricate field names; inspect v0.77.3 real sample to implement adapters.

## Example structured finding (synthetic)

```json
{
  "finding_id": "FND-001",
  "rule_id": "AEGIS-AUTORUN-001",
  "severity": "medium",
  "status": "needs_review",
  "attack": [{"technique_id": "T1547.001", "tactic": "persistence"}],
  "evidence_ids": ["EV-ID-FROM-DATABASE"],
  "limitations": ["File signature was not collected"]
}
```

The example above is a data contract, not a real result.
