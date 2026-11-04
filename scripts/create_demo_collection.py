#!/usr/bin/env python3
"""Generate harmless fictional evidence for offline parser demonstration."""
import argparse
import json
import zipfile
from pathlib import Path


SYNTHETIC = {
    'Windows.System.Pslist': [
        {'Name': 'explorer.exe', 'Pid': 3000, 'PPid': 1500,
         'Exe': r'C:\Windows\explorer.exe', 'CommandLine': 'explorer.exe'},
        {'Name': 'notepad.exe', 'Pid': 4000, 'PPid': 3000,
         'Exe': r'C:\Windows\System32\notepad.exe'},
    ],
    'Windows.Network.Netstat': [
        {'Pid': 3000, 'Protocol': 'TCP', 'Status': 'LISTEN',
         'Laddr': {'IP': '127.0.0.1', 'Port': 4455}, 'Raddr': {'IP': '0.0.0.0', 'Port': 0}},
    ],
    'Windows.System.Services': [
        {'Name': 'DemoService', 'DisplayName': 'Harmless Demo Service',
         'PathName': r'C:\Program Files\Demo\service.exe', 'State': 'Stopped', 'StartMode': 'Manual'},
    ],
    'Windows.Sys.StartupItems': [
        {'Name': 'Example Startup', 'Command': r'C:\Program Files\Demo\helper.exe',
         'Location': r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run', 'State': 'enabled'},
    ],
}


def create_zip(path: Path, artifacts=None):
    artifacts = SYNTHETIC if artifacts is None else artifacts
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, records in artifacts.items():
            payload = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records)
            archive.writestr(f'results/{name}%2FQuery.json', payload)
        archive.writestr('metadata.json', json.dumps({'note': 'synthetic fixtures only'}))
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', nargs='?', default='data/incoming/demo-collection.zip', type=Path)
    args = parser.parse_args()
    create_zip(args.output)
    print(f'Synthetic ZIP created: {args.output}')
