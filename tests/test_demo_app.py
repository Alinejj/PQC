
import unittest

from demo_app import (
    rsa_demo,
    rsa_signature_demo,
    ecdsa_demo,
    aes_demo,
    mlkem_demo,
    mldsa_demo,
    benchmark_demo,
)
from unittest.mock import patch


class TestDemoApp(unittest.TestCase):
    @patch("demo_app.subprocess.run")
    def test_benchmark_demo(self, mock_run):
        benchmark_demo()

        mock_run.assert_called_once()

        args, kwargs = mock_run.call_args

        self.assertIn("benchmark.py", args[0][1])
        self.assertIn("--iterations", args[0])
        self.assertTrue(kwargs["check"])

    
    @patch("builtins.print")
    def test_mlkem_key_exchange(self, mock_print):
        mlkem_demo()
        mock_print.assert_any_call("Secrets match:", True)

    @patch("builtins.print")
    def test_mldsa_signature(self, mock_print):
        mldsa_demo()
        mock_print.assert_any_call("Signature valid:", True)

    @patch("builtins.print")
    def test_rsa_key_exchange(self, mock_print):
        rsa_demo()
        mock_print.assert_any_call("Keys match:", True)

    @patch("builtins.print")
    def test_rsa_signature(self, mock_print):
        rsa_signature_demo()
        mock_print.assert_any_call("Signature valid:", True)

    @patch("builtins.print")
    def test_ecdsa_signature(self, mock_print):
        ecdsa_demo()
        mock_print.assert_any_call("Signature valid:", True)

    @patch("builtins.print")
    def test_aes_encryption(self, mock_print):
        aes_demo()
        mock_print.assert_any_call("Messages match:", True)


if __name__ == "__main__":
    unittest.main()
