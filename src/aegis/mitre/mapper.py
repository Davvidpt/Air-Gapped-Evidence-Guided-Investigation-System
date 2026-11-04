"""Small, pinned offline subset of ATT&CK IDs verified against official pages.

Not a full ATT&CK dataset; a rule's technique means a related technique,
not proof that a threat actor employed it.
"""
from __future__ import annotations

TECHNIQUES = {
    'T1547.001': {'name': 'Registry Run Keys / Startup Folder', 'tactics': ('persistence',), 'url': 'https://attack.mitre.org/techniques/T1547/001/'},
    'T1543.003': {'name': 'Windows Service', 'tactics': ('persistence', 'privilege-escalation'), 'url': 'https://attack.mitre.org/techniques/T1543/003/'},
    'T1059.001': {'name': 'PowerShell', 'tactics': ('execution',), 'url': 'https://attack.mitre.org/techniques/T1059/001/'},
}


def validate_mapping(technique_id: str | None, tactic: str | None) -> None:
    if technique_id is None:
        if tactic is not None:
            raise ValueError('Tactic tanpa technique ID tidak diperbolehkan')
        return
    if technique_id not in TECHNIQUES:
        raise ValueError(f'ATT&CK technique tidak dikenal dalam subset MVP: {technique_id}')
    if tactic not in TECHNIQUES[technique_id]['tactics']:
        raise ValueError(f'Tactic {tactic!r} tidak cocok dengan {technique_id}')
