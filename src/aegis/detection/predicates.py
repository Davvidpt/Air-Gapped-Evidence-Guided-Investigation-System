"""Auditable, non-executing predicates. Indicators are NOT malware confirmations."""
from __future__ import annotations

import re
from typing import Any

# Exact temp directory segments; exclude generic "temp" substrings in filenames.
TEMP_PATH = re.compile(r'(?i)(?:\\|/|%)(?:appdata\\local\\temp|windows\\temp|temp)(?:\\|/|%)')
RUN_LOCATION = re.compile(r'(?i)(?:\\currentversion\\run(?:once)?\b|\\startup(?:\\|/|$))')
ENC_ARG = re.compile(r'(?i)(?:^|\s)[-/](?:enc|encodedcommand|encodedc)\b')
PS_NAME = re.compile(r'(?i)(?:^|[\\/\s\"\'])((?:power)?shell|pwsh)\.exe(?:\b|\")')


def text(value: Any) -> str:
    return value if isinstance(value, str) else ''


def autorun_temp_path(row: dict) -> tuple[str, str] | None:
    command = text(row.get('command'))
    location = text(row.get('location'))
    if not (command and location and RUN_LOCATION.search(location) and TEMP_PATH.search(command)):
        return None
    return command, 'Startup melalui Run key/Startup Folder mengarah ke lokasi temporary yang perlu ditinjau.'


def service_temp_path(row: dict) -> tuple[str, str] | None:
    image = text(row.get('image_path'))
    if image and TEMP_PATH.search(image):
        return image, 'Konfigurasi Windows Service menunjuk ke lokasi temporary yang perlu ditinjau.'
    return None


def process_temp_path(row: dict) -> tuple[str, str] | None:
    executable = text(row.get('executable'))
    if executable and TEMP_PATH.search(executable):
        return executable, 'Proses aktif berada pada direktori temporary; bisa sah, perlu konteks tambahan.'
    return None


def powershell_encoded_command(row: dict) -> tuple[str, str] | None:
    command = text(row.get('command_line'))
    name = text(row.get('name')).lower()
    executable = text(row.get('executable'))
    is_powershell = name in ('powershell.exe', 'pwsh.exe') or bool(PS_NAME.search(executable))
    if is_powershell and command and ENC_ARG.search(command):
        # Store a truncated value; raw evidence is still accessible by evidence ID.
        return command[:512], 'PowerShell memakai parameter encoded command; penggunaan sah tetap mungkin.'
    return None


PREDICATES = {
    'autorun_temp_path': autorun_temp_path,
    'service_temp_path': service_temp_path,
    'process_temp_path': process_temp_path,
    'powershell_encoded_command': powershell_encoded_command,
}
