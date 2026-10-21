import argparse
import json
from dataclasses import asdict

from scanner.rules import load_rules
from scanner.walker import scan_path


def main():
    parser = argparse.ArgumentParser(
        description="Scan Python code for quantum-vulnerable cryptography"
    )
    parser.add_argument("target", help="file or folder to scan")
    parser.add_argument("--rules", default="rules/python_rules.json",
                        help="path to the rules JSON file")
    parser.add_argument("--json", action="store_true",
                        help="print findings as JSON instead of text")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    findings = scan_path(args.target, rules)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
        return

    for f in findings:
        print(f"{f.file}:{f.line}  [{f.status.upper()}] {f.algorithm} -> {f.replacement}")
    print(f"\n{len(findings)} finding(s)")


if __name__ == "__main__":
    main()