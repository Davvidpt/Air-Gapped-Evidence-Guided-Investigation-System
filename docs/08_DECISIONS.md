# 08 — Architecture Decision Records (ADRs)

## ADR-001: Single-host Python modular monolith

**Decision:** One Python application with SQLite and Streamlit on Debian VM. **Why:** 11-day solo delivery, low RAM, simpler reproducibility. **Tradeoff:** not for concurrent enterprise-scale processing.

## ADR-002: Bypass manual Velociraptor server import in operator workflow

**Decision:** Direct parse unencrypted ZIP in AEGIS. **Why:** eliminate manual CSV export, reduce operator actions. **Tradeoff:** must implement and test compatibility/metadata handling. Velociraptor GUI remains optional for expert verification.

## ADR-003: Preserve raw evidence and add normalized adapters incrementally

**Decision:** raw JSON always stored with source member and row; optional normalized entities. **Why:** flexible across artifact versions without silently discarding unknown data.

## ADR-004: Evidence-first rules, not LLM verdicts

**Decision:** severity and MITRE mappings come from explicit tested rules; Ollama only explains structured assessment. **Why:** auditability, reproducibility, offline support and lower hallucination risk.

## ADR-005: Profile-specific completeness

**Decision:** Coverage measures required artifacts actually available for a named profile, not percentage of threats detected. **Why:** honest interpretation of gaps.

## ADR-006: MVP supports unencrypted synthetic collections only

**Decision:** Explicitly document that X.509-encrypted containers are unsupported by current Python prototype. **Why:** deliver basic pipeline in time, do not mishandle encrypted evidence. Future approach: vetted Velociraptor decryption on a station that retains the private key before ingestion.

## ADR-007: No raw evidence or binary tools in public Git

**Decision:** commit source, documentation, specs and synthetic fixtures only. **Why:** privacy, licensing, executable trust and manageable repo size.
