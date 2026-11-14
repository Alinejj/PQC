import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from scanner.rules import load_rules
from scanner.walker import scan_path

from report_generator import generate_report

RULES_DIR = Path(__file__).resolve().parent / "rules"


def main():
    parser = argparse.ArgumentParser(
        description="Scan Python code for quantum-vulnerable cryptography"
    )
    parser.add_argument("target", help="file or folder to scan")
    parser.add_argument("--rules", default=None,
                        help="path to one rules JSON file (applies to Python files only)")
    parser.add_argument("--json", action="store_true",
                        help="print findings as JSON instead of text")
    parser.add_argument(
        "--report",
        action="store_true",
        help="generate a detailed security report"
    )
    args = parser.parse_args()

    if args.rules:
        rules = load_rules(args.rules)
        config_rules = {}
    else:
        rules = load_rules(str(RULES_DIR / "python_rules.json"))
        config_rules = {
            "nginx": load_rules(str(RULES_DIR / "nginx_rules.json")),
            "openssl": load_rules(str(RULES_DIR / "openssl_rules.json")),
        }

    try:
        findings = scan_path(args.target, rules, config_rules)
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(2)

    if args.report:
        generate_report(findings)
        return

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
        return

    for f in findings:
        print(f"{f.file}:{f.line}  [{f.status.upper()}] {f.algorithm} -> {f.replacement}")
    print(f"\n{len(findings)} finding(s)")


if __name__ == "__main__":
    main()