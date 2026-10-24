
import io
import unittest
from contextlib import redirect_stdout

from report_generator import generate_report
from scanner.finding import Finding


class TestReportGenerator(unittest.TestCase):

    def capture_report(self, findings):
        output = io.StringIO()

        with redirect_stdout(output):
            generate_report(findings)

        return output.getvalue()

    def test_empty_findings(self):
        report = self.capture_report([])

        self.assertIn("Total Findings: 0", report)
        self.assertIn(
            "No cryptographic algorithms detected.",
            report
        )

    def test_vulnerable_finding(self):
        finding = Finding(
            file="example.py",
            line=10,
            matched_text="rsa.generate_private_key",
            algorithm="RSA",
            category="asymmetric",
            status="vulnerable",
            replacement="ML-KEM or ML-DSA"
        )

        report = self.capture_report([finding])

        self.assertIn("Total Findings: 1", report)
        self.assertIn("Vulnerable: 1", report)
        self.assertIn("RSA", report)
        self.assertIn("ML-KEM or ML-DSA", report)

    def test_multiple_statuses(self):
        findings = [
            Finding(
                file="example.py",
                line=5,
                matched_text="rsa.generate_private_key",
                algorithm="RSA",
                category="asymmetric",
                status="vulnerable",
                replacement="ML-KEM or ML-DSA"
            ),
            Finding(
                file="example.py",
                line=15,
                matched_text="hashlib.md5",
                algorithm="MD5",
                category="hash",
                status="weak",
                replacement="SHA-256"
            )
        ]

        report = self.capture_report(findings)

        self.assertIn("Total Findings: 2", report)
        self.assertIn("Vulnerable: 1", report)
        self.assertIn("Weak: 1", report)


if __name__ == "__main__":
    unittest.main()
