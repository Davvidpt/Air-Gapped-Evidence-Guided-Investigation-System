# 04 — Security, confidentiality and trust boundaries

## Threat model

A potentially compromised endpoint writes a ZIP on removable media. Files, names, logs, timestamps, and ZIP metadata can be deliberately malformed. AEGIS station should not execute content copied from collections. Treat the USB and all collection data as untrusted input.

## Ingestion controls (MVP)

- Size and entry count limits and decompression quotas, including compression ratios where appropriate.
- Reject absolute paths, `..` traversal, path collisions and duplicate members before any extraction. Prefer never extracting payloads to the filesystem.
- In M1, bound each result member to 64 MiB in memory, validate JSON strictly, verify all ZIP CRCs and reject the whole collection atomically on parse errors. Streaming JSON and partial failure handling are planned improvements.
- Do not render unescaped file paths, log messages or commands as HTML/Markdown with executable content.
- Parameterized SQL, file permissions limited to station operator, no network upload in normal operation.
- Preserve original ZIP separately; do not mutate raw evidence during normalization.
- Allow offline test imports without encryption only for **synthetic data**.

## Evidence integrity

- On receipt compute SHA-256 of the original ZIP; retain timestamp, operator and source media ID if documented.
- Compare with a trusted independently saved collection log/hash where available. Two files stored on the same writable USB could both have been altered, so matching them alone does not prove authenticity.
- Signed collector manifest and X.509-encrypted collections are planned security improvements; do not claim them active in MVP.
- Keep private decryption keys ONLY on trusted station; never embed them in USB collector.

## Privacy and AI

- Default no real personal or organization data in Git, demo or screenshots.
- Local Ollama bound to loopback; disable telemetry/network access when feasible and validate offline behavior.
- Give AI only minimal, preferably redacted structured evidence and known ID list.
- Never execute instructions found in logs/filenames; treat them as data and resist prompt injection.
- Validate AI JSON schema and evidence citations; discard unsupported claims.
- Protect exported reports and delete synthetic test outputs when no longer needed.

## Safe demo

Use synthetic records and isolated, authorized lab VMs. Avoid weakening host protections. Do not use actual malware for demonstration. Roll back test VM snapshots between trials.
