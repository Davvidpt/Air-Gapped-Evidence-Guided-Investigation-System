# 12 — M2 Deterministic Detection + ATT&CK Mapping (2026-11-03)

## Status and scope

M2 adds a **review-oriented** assessment to the successful M1 ZIP ingestion pipeline. It does not assert malware, attribute a threat actor, identify C2 automatically, or prove a machine is clean. The rule set is deliberately narrow and uses only M1's four normalized artifact types.

Already validated on authorized test input in the user's lab: M1 imported 1,138 rows (458 Pslist, 314 Netstat, 292 Services, 74 StartupItems) with collection ID **2**. M2 has **not** been verified on that specific collection until the operator runs the commands below.

## Upgrade an existing M1 installation

Run on Debian in `~/AEGIS_M1`, using a verified backup destination:

```bash
cd ~/AEGIS_M1
cp -p data/aegis-v1.db data/aegis-v1.db.before-m2
# Copy AEGIS_M2_Patch.zip into your home directory, then:
unzip -o ~/AEGIS_M2_Patch.zip -d .
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m aegis inspect-fields --db data/aegis-v1.db --collection 2
PYTHONPATH=src python3 -m aegis assess --db data/aegis-v1.db --collection 2
PYTHONPATH=src python3 -m aegis summary --db data/aegis-v1.db --collection 2
```

The database connection automatically performs the additive schema migration **v1 → v2**, preserving `collections`, `artifact_runs`, and `evidence`. New tables: `assessment_runs`, `findings`. The migration does not re-ingest any ZIP or modify raw evidence rows. **Do not downgrade M2 source code and open a v2 DB in M1**, because M1 rejects schema versions other than v1.

## Commands

- `ingest <zip> --db <db>`: original atomic M1 ingestion
- `summary --db <db> --collection <id>`: imported counts and number of assessments
- `inspect-fields --db <db> --collection <id>`: normalized field counts, **without showing private field contents**
- `assess --db <db> --collection <id> --rules rules/detection.json`: rule matching + durable evidence-linked findings
- `assess ... --json`: structured output for dashboard (includes raw observed values: treat as sensitive)

Rules are a JSON file only for this zero-external-dependency milestone. An example YAML file in `rules/` is documentation only, not executed. The declared `predicate` must be one of the explicit Python functions in `src/aegis/detection/predicates.py`; arbitrary Python expressions and `eval` are never accepted.

## Initial rules and conservative semantics

| Rule ID | Test | Severity | Related ATT&CK |
|---|---|---|---|
| AEGIS-AUTORUN-001 | Run key/Startup Folder entry references Windows/user Temp directory | Medium | T1547.001 (persistence) |
| AEGIS-SERVICE-001 | Windows Service image path references Temp directory | Medium | T1543.003 (persistence) |
| AEGIS-PROCESS-001 | Active process executable path references Temp directory | Low | Unmapped (path alone insufficient) |
| AEGIS-POWERSHELL-001 | PowerShell process includes encoded-command flag | Medium | T1059.001 (execution) |

**One row matching a rule is only an indicator for review.** A mapped technique is an association, not proof of malicious use, persistence establishment, or compromise. Events that have ended before collection can be missed by these snapshot artifacts. False positives are possible (installers, administrative automation, normal updates).

Pinned, **small manually curated** offline mapping validated against official MITRE pages on November 3, 2026. **Not a complete or downloaded ATT&CK STIX release.**

- https://attack.mitre.org/techniques/T1547/001/
- https://attack.mitre.org/techniques/T1543/003/
- https://attack.mitre.org/techniques/T1059/001/

## Source evidence link

`findings.evidence_id` references `evidence.evidence_id` with a database foreign key. Evidence IDs are stable fingerprints from ZIP hash + member + source row (M1). `observed_value` is stored for review in private database; CLI defaults to displaying only evidence ID prefix and rule ID. `--json` includes sensitive values.

## Coverage vs quality

`Quick profile: 4/4` means only that all four kinds of artifact results exist. It does **not** mean all query columns populated, that every command succeeded, or that all threats would be detected.

`inspect-fields` reports normalized field presence. Check especially `Windows.Sys.StartupItems` command/location, `Windows.System.Services` image_path, and `Windows.System.Pslist` executable/command_line. If those are 0 or unexpectedly sparse, adapters must be revised **before drawing conclusions** from `NO_RULE_MATCHES`.

## Security, privacy and limitations

- Use only authorized, non-sensitive lab data while raw ZIP and SQLite are unencrypted.
- Do not publish raw ZIP, the DB, JSON dumps, or paths containing real account information.
- Original ZIPs remain the authoritative data; SHA-256 after import is **not** an authenticity signature.
- Avoid destructive cleanup during investigation; preserve raw evidence.
- Windows Defender protection should remain enabled in host/VM labs.
- M2 does not run collected commands or extract executables.
- The current parser still rejects encrypted ZIPs; designing secure offline decrypt/import is a later milestone.
- The initial rules are not production-quality malware signatures or validated detection coverage.

## M2 acceptance criteria

1. All M1 and M2 unit tests pass (19 tests in the build environment).
2. Previously imported collection ID 2 remains available after migration.
3. `inspect-fields` shows whether the four normalized adapters populate key fields.
4. `assess` runs and stores findings, each linked to `evidence.evidence_id`.
5. Re-running with identical rules is idempotent (returns an existing assessment).
6. No matches is rendered as `NO_RULE_MATCHES`, never `SAFE` or `CLEAN`.

## Next milestone

M3 should build a minimal Streamlit dashboard reading SQLite read-only, display evidence references and field coverage, and generate a static Indonesian HTML/PDF report. After that, integrate optional Ollama AI explanations that are limited to validated findings and cannot edit severity/ATT&CK IDs.

## Optional reproducible positive demo (fictional data only)

```bash
python3 scripts/create_assessment_demo.py data/incoming/synthetic-indicators.zip
PYTHONPATH=src python3 -m aegis ingest data/incoming/synthetic-indicators.zip --db data/m2-demo.db
PYTHONPATH=src python3 -m aegis assess --db data/m2-demo.db --collection 1
```

Expected: four fictional review indicators, three related ATT&CK technique IDs; no malware is executed or supplied. This demo tests **rule functionality**, not threat detection accuracy.
