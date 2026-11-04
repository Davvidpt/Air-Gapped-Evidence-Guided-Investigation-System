# 09 — Submission and demo checklist

## Repository

- [ ] Clear README, architecture diagram, quickstart, requirements and supported OS.
- [ ] Collector profile/spec documented; Velociraptor attribution and versions recorded.
- [ ] MITRE data snapshot version and source cited.
- [ ] All screenshots/data are synthetic or appropriately redacted and authorized.
- [ ] Security limitations, false positive possibilities and coverage semantics explained.
- [ ] Reproducible demo commands and fixture package included.
- [ ] Tests run and recorded; no secrets or endpoint ZIPs in Git.

## Video (proposed 5–7 minutes, adjust to actual competition rules)

1. Operational problem in offline/air-gapped context.
2. Show USB collector generating offline ZIP from lab Windows VM.
3. Copy ZIP to Debian station; upload directly, no manual Velociraptor import.
4. View rule finding and click evidence/member/row.
5. Show ATT&CK mapping and visible evidence gaps.
6. Show AI explanation if stable; disable AI to prove core works anyway.
7. Export an Indonesian report and show testing metrics/limitations.

## Slides (suggested)

Problem → Existing approaches / differentiation → Architecture → Actual workflow → Detection logic and provenance → ATT&CK mapping → AI controls → Demo evidence & measured results → Limitations → Deployment potential.

## Pre-submit audit

- [ ] Confirm current official submission format, limits and deadline.
- [ ] Project link accessible by reviewers.
- [ ] Demo has no real private data or misleading security assurance.
- [ ] Include author contribution and third-party tool attribution.
