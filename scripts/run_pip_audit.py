#!/usr/bin/env python
"""Run pip-audit and write results to logs/pip-audit-latest.txt."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / 'logs'
LOG_FILE = LOG_DIR / 'pip-audit-latest.txt'


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, '-m', 'pip_audit', '--format', 'columns']
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    output = (proc.stdout or '') + (proc.stderr or '')
    header = f"# pip-audit exit code: {proc.returncode}\n\n"
    LOG_FILE.write_text(header + output, encoding='utf-8')
    print(output)
    print(f"\nWrote {LOG_FILE}")
    return proc.returncode


if __name__ == '__main__':
    raise SystemExit(main())
