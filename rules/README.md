# Detection rules

YAML should define descriptive fields and IDs, and reference **named, tested Python predicates**. Never dynamically `eval()` rule text or generate code from model output. All rules require positive and negative fixtures and an explicit ATT&CK mapping justification.
