# AEGIS — Air-Gapped Evidence & Guided Investigation System

**Build:** v0.2.0 — M1 ZIP ingestion + M2 deterministic assessment and limited ATT&CK mapping. **Not yet implemented:** Streamlit dashboard, PDF report, local AI, and advanced correlation.

AEGIS processes Velociraptor Offline Collector ZIPs **without needing Server.Utils.ImportCollection**. It is a defensive workflow for authorized Windows lab endpoints and produces reviewable *indicators*, not infection verdicts.

## Components

`USB Velociraptor collector → ZIP → bounded Python validation/JSONL ingestion → SQLite raw + normalized evidence → named detection predicates → related MITRE ATT&CK IDs → evidence-linked findings`

A local AI assistant and dashboard are future milestones and **must not override** deterministic findings. No online calls are made by the current source code.

## Requirements

Debian 12+; Python 3.10+; standard library only; authorized lab ZIP not encrypted. The importer has deliberate archive size limits (350 MiB uncompressed, 64 MiB per result member, 2,000 entries).

## Quickstart

```bash
cd ~/AEGIS_M1
# Use an existing M1 database (back it up before deploying M2), or create synthetic data:
python3 scripts/create_demo_collection.py data/incoming/demo-collection.zip
PYTHONPATH=src python3 -m aegis ingest data/incoming/demo-collection.zip --db data/aegis-v1.db
PYTHONPATH=src python3 -m aegis inspect-fields --db data/aegis-v1.db --collection 1
PYTHONPATH=src python3 -m aegis assess --db data/aegis-v1.db --collection 1
PYTHONPATH=src python3 -m aegis summary --db data/aegis-v1.db --collection 1
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

For a **previously imported real lab collection ID 2**, do not reimport:

```bash
PYTHONPATH=src python3 -m aegis inspect-fields --db data/aegis-v1.db --collection 2
PYTHONPATH=src python3 -m aegis assess --db data/aegis-v1.db --collection 2
PYTHONPATH=src python3 -m aegis summary --db data/aegis-v1.db --collection 2
```

**Always interpret `NO_RULE_MATCHES` as no rules matched this limited evidence; not as clean.** Artifact presence (4/4) also does not imply field completeness.

## Documentation

- `docs/01_ARCHITECTURE.md` — architecture overview
- `docs/02_DATA_CONTRACT.md` — M1 evidence schema
- `docs/03_DETECTION_AND_MITRE.md` — detection philosophy
- `docs/04_SECURITY_PRIVACY.md` — data handling cautions
- `docs/11_M1_IMPLEMENTATION.md` — M1 baseline
- **`docs/12_M2_IMPLEMENTATION.md` — M2 migration, rules, commands, limitations, acceptance tests**

Source contains no malware, private endpoint ZIPs or model weights. Existing `.gitignore` excludes evidence files and databases.
