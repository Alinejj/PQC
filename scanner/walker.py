import os
from pathlib import Path

from scanner.scan_python import scan_file
from scanner.scan_ast import scan_file_ast

SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules"}

# file extension -> which config rule set applies to it
CONFIG_EXTENSIONS = {".conf": "nginx", ".cnf": "openssl"}


def dedupe(findings):
    seen = set()
    merged = []
    for finding in findings:
        key = (finding.file, finding.line, finding.algorithm)
        if key not in seen:
            seen.add(key)
            merged.append(finding)
    merged.sort(key=lambda f: (f.file, f.line))
    return merged


def scan_one(path, rules):
    return dedupe(scan_file_ast(path, rules) + scan_file(path, rules))


def config_kind(path):
    return CONFIG_EXTENSIONS.get(Path(path).suffix.lower())


def scan_any(path, rules, config_rules):
    kind = config_kind(path)
    if kind in config_rules:
        # config files are not Python, so only the regex pass applies
        return dedupe(scan_file(path, config_rules[kind]))
    return scan_one(path, rules)


def scan_path(target, rules, config_rules=None):
    target = Path(target)
    if not target.exists():
        raise FileNotFoundError(f"path not found: {target}")
    config_rules = config_rules or {}

    if target.is_file():
        return scan_any(target, rules, config_rules)

    findings = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py") or config_kind(name) in config_rules:
                findings.extend(scan_any(os.path.join(root, name), rules, config_rules))
    return findings