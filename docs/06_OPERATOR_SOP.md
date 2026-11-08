# 06 — One-page operator SOP (draft, laboratory only)

## Goal

Collect and triage a Windows lab endpoint offline without needing to understand raw logs.

## Before collection

1. Ensure authorization and correct endpoint identity.
2. Use collector prepared by a trusted station; verify its hash against a separately retained baseline.
3. Confirm USB space and sanitized lab contents. Do not use a USB from an untrusted machine on another endpoint without approved inspection.
4. Record operator, target label, and local time. Treat host clock as potentially inaccurate.

## On Windows endpoint

1. Keep normal protections enabled; do not run unknown executable samples.
2. Connect the USB; launch the approved collector manually as Administrator (Windows does not auto-run USB collector by default).
3. Wait for completion; note any errors. Do not interpret the absence of rows as no threat.
4. Verify the ZIP and log files exist; remove USB safely.

## At AEGIS station

1. Copy ZIP and associated log to a protected import area.
2. Jalankan `bash scripts/run_dashboard.sh`, buka localhost:8501 melalui SSH tunnel, lalu Import ZIP. CLI `aegis ingest` tetap tersedia.
3. Pilih collection, audit artifact/field pada Ringkasan, jalankan assessment, lalu tinjau Temuan, MITRE dan Evidence.
4. Pada sidebar pilih assessment aktif, kemudian buka halaman Laporan dan ekspor PDF. Catat pertanyaan investigasi yang masih perlu dijawab.
5. Preserve original ZIP for authorized review. Never upload it to a public repository.

## Interpretation

- `No actionable findings` ≠ `device safe`.
- `Partial evidence` means visibility is limited.
- `Needs review` indicates a rule match, not confirmed infection.

For production deployments, use encrypted collection, written handling procedures, and operator access control.
