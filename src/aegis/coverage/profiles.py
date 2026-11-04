"""Collection profile coverage is NOT a security cleanliness percentage."""
from __future__ import annotations

QUICK_ARTIFACTS = (
    'Windows.System.Pslist',
    'Windows.Network.Netstat',
    'Windows.System.Services',
    'Windows.Sys.StartupItems',
)


def quick_coverage(observed_artifacts: set[str]) -> dict:
    present = [name for name in QUICK_ARTIFACTS if name in observed_artifacts]
    missing = [name for name in QUICK_ARTIFACTS if name not in observed_artifacts]
    return {'profile': 'quick', 'present': present, 'missing': missing, 'required': len(QUICK_ARTIFACTS)}
