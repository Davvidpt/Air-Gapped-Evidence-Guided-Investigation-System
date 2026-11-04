# 03 — Detection logic, confidence and MITRE ATT&CK

## Philosophy

Rules flag **conditions to review**, not confirmed compromise. A single service/startup/task is normal unless contextual checks elevate concern. `No actionable findings` must never be shown as `known clean`.

## Minimal rule contract

```yaml
id: AEGIS-AUTORUN-001
version: 1
name: Startup command in user-writable temporary location
source_artifacts: [Windows.Sys.StartupItems]
condition: adapter_specific_predicate
severity: medium
techniques:
  - id: T1547.001
    tactic: persistence
explanation: Review command, file hash, signer and allowlist before concluding anything.
```

This example is **not** a ready-to-use detection implementation. It requires an explicit, tested predicate; rule definitions are parsed as data, never `eval`ed.

## Evidence-first rule backlog

1. Startup entry executing from an unusual user-writable/temporary location — T1547.001 when startup mechanics are evidenced.
2. Service executable path outside expected program/system locations with other suspicious context — T1543.003 when service configuration is evidenced.
3. Process running from unusual temporary path — anomaly only; do not assign T1059 merely because a filename is unusual.
4. Scheduled task launching executable from unusual path — T1053.005; requires TaskScheduler data.
5. Permanent WMI subscription — T1546.003 when corresponding WMI data is collected.
6. Command shell execution — T1059.003 **only** with process creation/command evidence; do not infer from an unrelated log.

At MVP start, only rules supported by actually collected fields are enabled. Extra rules are feature-gated until their artifacts exist and are tested. Avoid unvalidated global risk percentages.

## Coverage semantics

Coverage is `collected_required_artifacts / planned_required_artifacts` **within a declared collection profile**, plus `complete|partial|unavailable` per artifact. This is *not* a percentage of attacks detected or a measure of malware-free confidence. Missing event logs and protected process data are visible gaps.

## MITRE mapping

- Use MITRE official Enterprise STIX dataset from https://github.com/mitre-attack/attack-stix-data
- Pin exact release in a manifest with dataset SHA-256 and license notice.
- Validate technique ID exists, not revoked/deprecated, and relevant tactic association when possible.
- Map rule -> technique with provenance and version. Do not allow AI to invent technique IDs.
- Heatmap shades **supported findings**, not general network attack coverage.

## Cross-endpoint correlation (stretch)

Initial correlation can compare normalized SHA-256, file path, autorun command or USB device identifier when actually available. Shared value is a correlation candidate, not proof of propagation. Show which evidence from which endpoints supports the link.
