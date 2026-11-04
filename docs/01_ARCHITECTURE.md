# 01 — Architecture and module boundaries

## System context

Windows endpoints are surveyed with an operator-launched Velociraptor offline collector. The collector writes ZIP and log locally. A physically separate Linux station receives the archive (USB or trusted local copy), analyzes it without the network, and presents an assessment in Indonesian.

## End-to-end processing

1. Receive ZIP in **quarantine/incoming**, never auto-run content.
2. Validate archive structure, size quotas, encryption mode, CRC, and SHA-256.
3. Identify artifact result members from `results/`. Preserve collection metadata and warnings where available. Store ZIP hash and original path.
4. Decode Velociraptor JSON rows (often newline-delimited JSON in `.json` files). Parse artifact and query names separated by `%2F` in member paths.
5. Create a stable `evidence_id`; save raw JSON, source member, 1-based row number, timestamps when explicit, and collection ID.
6. Run artifact-specific normalization. Unknown artifacts remain importable as raw evidence.
7. Apply deterministic rules and coverage checks; results reference actual evidence IDs.
8. Validate rule ATT&CK IDs from a locally pinned Enterprise dataset. Generate assessment independent of LLM.
9. Optionally produce AI explanation of validated findings and recognized limitations, with references only to existing evidence IDs.
10. Show dashboard and export report. Nothing sends endpoint evidence to an external API.

## Modules, responsibilities and boundaries

| Module | Input | Output | Explicit non-responsibility |
|---|---|---|---|
| ingestion | ZIP path | package + raw artifact rows | No malware verdict |
| normalization | raw rows | normalized entities with provenance | No high-level verdict |
| storage | events/entities | SQLite records | No threat classification |
| detection | normalized entities + rules | findings + rule ID + evidence IDs | No invented indicators |
| coverage | profile, collected/missing/failed artifacts | profile coverage + warnings | Not threat detection effectiveness |
| mitre | rule-linked technique IDs | validated ATT&CK mappings | No free-form LLM mapping |
| correlation | independent endpoint collections | shared indicators / contextual links | No automatic claim of lateral movement |
| ai | validated findings, redacted context | human-readable explanation | No primary severity or evidence fabrication |
| ui/reporting | persisted assessment | dashboard, HTML/PDF | No hidden re-analysis |

## Runtime architecture

Single Debian VM; Python process running Streamlit in localhost/LAN-restricted mode; SQLite file. Prototype ingestion CLI runs without the UI for repeatable tests. Ollama is strictly optional and bound to localhost when installed. No Docker or microservice requirement for MVP.

## Failure behavior

- Invalid/oversized archive: reject, record reason, preserve original separately.
- Unsupported format/encrypted ZIP: mark as unsupported, do not silently say clean.
- M1: malformed result member causes rollback of the entire import; partial retention is planned after provenance and coverage rules are implemented.
- Missing artifact: show not_collected, not zero findings.
- AI failure/time-out: assessment and PDF still work without AI text.
