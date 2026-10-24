
from collections import Counter


def generate_report(findings):
    """Generate a readable security report from scanner findings."""

    print("=" * 50)
    print("CRYPTOGRAPHIC SECURITY REPORT")
    print("=" * 50)

    print(f"\nTotal Findings: {len(findings)}")

    # Count findings by security status
    status_counts = Counter(f.status for f in findings)

    print("\nSECURITY SUMMARY")
    print("-" * 50)

    for status in ["vulnerable", "weak", "transitional", "safe"]:
        count = status_counts.get(status, 0)
        print(f"{status.capitalize()}: {count}")

    print("\nDETAILED FINDINGS")
    print("-" * 50)

    if not findings:
        print("No cryptographic algorithms detected.")

    for index, finding in enumerate(findings, start=1):
        print(f"\n[{index}] {finding.algorithm}")
        print(f"    File: {finding.file}")
        print(f"    Line: {finding.line}")
        print(f"    Category: {finding.category}")
        print(f"    Status: {finding.status.upper()}")
        print(f"    Matched Code: {finding.matched_text}")
        print(f"    Recommendation: {finding.replacement}")

    print("\n" + "=" * 50)
    print("END OF REPORT")
    print("=" * 50)
