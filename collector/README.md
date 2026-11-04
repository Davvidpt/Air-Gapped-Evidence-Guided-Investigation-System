# Collector specifications and compatibility

- Version used in prototype: Velociraptor v0.77.3.
- Basic collector artifacts tested earlier: `Windows.System.Pslist`, `Windows.Network.Netstat`, `Windows.System.Services`, `Windows.Sys.StartupItems`.
- Keep reproducible `spec.yaml` exported from Velociraptor under `collector/specs/`; inspect for credentials/secrets before committing.
- Proposed deep profile additions only after confirming exact artifact names in the installed repository: Scheduled Tasks, Prefetch, BAM, Amcache, registry persistence, Windows event logs.
- Track artifact, resource cost, reason for inclusion, expected fields, and detection rule depending on it in documentation.
- Do not commit `.exe` or private certificate keys. For tests use non-encrypted synthetic results; for real data plan X.509 encryption and trusted station decryption.
