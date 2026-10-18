import argparse

from scanner.rules import load_rules
from scanner.walker import scan_path


def main():
    parser = argparse.ArgumentParser(
        description="Scan Python code for quantum-vulnerable cryptography"
    )
    parser.add_argument("target", help="file or folder to scan")
    parser.add_argument("--rules", default="rules/python_rules.json",
                        help="path to the rules JSON file")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    findings = scan_path(args.target, rules)

    for f in findings:
        print(f"{f.file}:{f.line}  [{f.status.upper()}] {f.algorithm} -> {f.replacement}")
    print(f"\n{len(findings)} finding(s)")


if __name__ == "__main__":
    main()