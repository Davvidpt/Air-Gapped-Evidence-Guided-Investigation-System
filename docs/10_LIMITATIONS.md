# 10 — Limitations and responsible claims

1. Offline endpoint collection is not novel by itself; Velociraptor provides the underlying feature.
2. AEGIS is not an antivirus, EDR, or full forensic lab replacement.
3. A detection rule match signals a condition for review and does not prove malicious activity.
4. Absence of findings does not prove the device uncompromised.
5. Collection after reboot/shutdown may omit volatile evidence; missing Windows logging limits retrospective analysis.
6. SHA-256 computed on receipt establishes identity/fixity from that moment, not trusted provenance without an independent baseline/signature.
7. M1 ingestion implementation does not support encrypted collection ZIPs, all artifact schemas, EVTX parsing, full cross-endpoint analytics, or real AI.
8. Model summaries may be wrong; they must be limited to referenced evidence and should be distinctly labeled as AI-generated.
9. Evaluation metrics on synthetic fixtures cannot establish accuracy against unknown real attacks.
10. A fully air-gapped deployment must pre-stage binaries, rule content, ATT&CK snapshot, Python dependencies and model files while preserving license obligations.
