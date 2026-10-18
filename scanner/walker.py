import os
from pathlib import Path

from scanner.scan_python import scan_file
from scanner.scan_ast import scan_file_ast

SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules"}


def scan_one(path, rules):
    seen = set()
    merged = []
    for finding in scan_file_ast(path, rules) + scan_file(path, rules):
        key = (finding.file, finding.line, finding.algorithm)
        if key not in seen:
            seen.add(key)
            merged.append(finding)
    merged.sort(key=lambda f: (f.file, f.line))
    return merged


def scan_path(target, rules):
    target = Path(target)
    if target.is_file():
        return scan_one(target, rules)

    findings = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                findings.extend(scan_one(os.path.join(root, name), rules))
    return findings