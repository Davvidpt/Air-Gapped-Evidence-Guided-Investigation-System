#!/usr/bin/env python3
"""Harmless, fictional result rows for demonstrating four review indicators.
This does not run or distribute any executables or commands.
"""
import argparse
from pathlib import Path
if __package__:
    from .create_demo_collection import create_zip
else:
    from create_demo_collection import create_zip

FAKE_RESULTS = {
    'Windows.Sys.StartupItems': [
        {'Name': 'FictionalStartup', 'Location': r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run',
         'Command': r'C:\Users\Lab\AppData\Local\Temp\example-app.exe', 'State': 'enabled'}
    ],
    'Windows.System.Services': [
        {'Name': 'FictionalService', 'PathName': r'C:\Windows\Temp\sample-service.exe',
         'State': 'Stopped', 'StartMode': 'Manual'}
    ],
    'Windows.System.Pslist': [
        {'Name': 'example-app.exe', 'Exe': r'C:\Users\Lab\AppData\Local\Temp\example-app.exe'},
        {'Name': 'powershell.exe', 'Exe': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
         'CommandLine': 'powershell.exe -EncodedCommand ZABlAG0AbwA='}
    ],
    'Windows.Network.Netstat': [
        {'Pid': 42, 'Protocol': 'TCP', 'Status': 'LISTEN',
         'Laddr': {'IP': '127.0.0.1', 'Port': 1234}, 'Raddr': {'IP': '0.0.0.0', 'Port': 0}}
    ],
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', nargs='?', type=Path,
                        default=Path('data/incoming/synthetic-indicators.zip'))
    args = parser.parse_args()
    create_zip(args.output, FAKE_RESULTS)
    print(f'Created fictional demonstration ZIP: {args.output}')
