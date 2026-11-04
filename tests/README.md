# Tests

Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` from repo root. No third-party test package required.

Tests cover synthetic four-artifact evidence; stored provenance, normalization, duplicate import, missing artifact coverage, unknown artifact raw retention, invalid JSON rollback, unsafe paths, duplicate ZIP members, JSON array parsing, and size quotas. In addition, test with a real *authorized lab* ZIP from Velociraptor v0.77.3 before declaring format compatibility proven.
