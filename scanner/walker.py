import os
from pathlib import Path

from scanner.scan_python import scan_file

SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules"}


def scan_path(target, rules):
    target = Path(target)
    if target.is_file():
        return scan_file(target, rules)

    findings = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                findings.extend(scan_file(os.path.join(root, name), rules))
    return findings