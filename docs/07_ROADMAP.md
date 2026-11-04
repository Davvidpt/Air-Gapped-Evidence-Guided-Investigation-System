# 07 — 11-day execution roadmap (4–14 November 2026)

## Delivery strategy

One developer, 16 GB Windows host RAM, one Debian station VM, one Windows lab VM. Use existing Velociraptor v0.77.3 collector. Prioritize vertical end-to-end features over number of tools. Do not start Wazuh, Timesketch, OpenCTI or extensive UI frameworks.

| Date | Deliverable | Acceptance gate |
|---|---|---|
| Nov 4 | Validate M1 package against genuine v0.77.3 lab ZIP | 4 existing artifacts visible without Server.Utils.ImportCollection |
| Nov 5 | Finish ingestion compatibility + fixes | Re-import idempotent; row references stable |
| Nov 6 | Artifact adapters and 3 tested rules | Positive and negative fixtures pass |
| Nov 7 | Coverage engine + pinned ATT&CK mapping | Missing artifacts flagged; valid technique IDs only |
| Nov 8 | Minimal Streamlit dashboard | Upload ZIP -> Findings -> Raw Evidence |
| Nov 9 | Indonesian HTML/PDF report | One-click report with traceable evidence |
| Nov 10 | Collector quick/deep profiles (only tested additions) | Fresh ZIP imports; logs and completeness tracked |
| Nov 11 | Optional Ollama integration | AI answer grounded in provided evidence IDs; deterministic fallback works |
| Nov 12 | Offline end-to-end regression + measures | Tests recorded, false positives and limitations documented |
| Nov 13 | Demo video, README, diagram, slides | Run reproducible script/demo without internet |
| Nov 14 | Submission freeze and backup | Final files/links audited and submitted |

**If delayed:** cut AI first, then cross-endpoint correlation; keep ingestion, reliable findings, MITRE, dashboard, report and tests.

## Change control

At end of Nov 8: prohibit new architectural components; only defects, test coverage, docs and essential extensions. Keep a daily change log in Git commits.
