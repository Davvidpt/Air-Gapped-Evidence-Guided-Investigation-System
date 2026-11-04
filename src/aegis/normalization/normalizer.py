"""Conservative, non-lossy normalized views; raw JSON remains authoritative."""
from __future__ import annotations

from typing import Any


def _get(data: dict, *keys: str) -> Any:
    # Names are case-insensitive only; no guesses when a key is absent.
    by_lower = {str(key).lower(): value for key, value in data.items()}
    for key in keys:
        value = by_lower.get(key.lower())
        if value is not None:
            return value
    return None


def normalize(artifact: str, record: dict) -> tuple[str | None, dict | None]:
    """Return (entity_type, fields); unknown artifacts remain raw-only."""
    if artifact == 'Windows.System.Pslist':
        return 'process', {
            'name': _get(record, 'Name', 'ProcessName'),
            'pid': _get(record, 'Pid', 'PID'),
            'ppid': _get(record, 'Ppid', 'PPid', 'ParentPid'),
            'executable': _get(record, 'Exe', 'Path', 'Executable'),
            'command_line': _get(record, 'CommandLine', 'Cmdline'),
        }
    if artifact == 'Windows.Network.Netstat':
        return 'connection', {
            'pid': _get(record, 'Pid', 'PID'),
            'protocol': _get(record, 'Protocol', 'Proto'),
            'state': _get(record, 'Status', 'State'),
            'local_address': _get(record, 'Laddr', 'LocalAddr', 'LocalAddress'),
            'remote_address': _get(record, 'Raddr', 'RemoteAddr', 'RemoteAddress'),
        }
    if artifact == 'Windows.System.Services':
        return 'service', {
            'name': _get(record, 'Name', 'ServiceName'),
            'display_name': _get(record, 'DisplayName'),
            'image_path': _get(record, 'PathName', 'ImagePath', 'BinaryPathName'),
            'state': _get(record, 'State', 'Status'),
            'start_mode': _get(record, 'StartMode', 'StartType'),
        }
    if artifact == 'Windows.Sys.StartupItems':
        return 'autorun', {
            'name': _get(record, 'Name', 'Entry'),
            'command': _get(record, 'Command', 'Path'),
            'location': _get(record, 'Location'),
            'user': _get(record, 'User'),
            'state': _get(record, 'State', 'Enabled'),
        }
    return None, None
