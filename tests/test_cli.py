"""Tests for the command-line interface."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from cli import main

USAGE_ERROR_CODE = 2


def run_cli(*argv):
    """Run the CLI and return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(list(argv))
        except SystemExit as exit_info:
            code = exit_info.code
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    """End-to-end tests of the command-line interface."""

    def test_prints_key_value_pairs(self):
        code, out, _ = run_cli("-p", "express", "-d", "2", "-f", "dev")
        self.assertEqual(code, 0)
        self.assertIn("package: express", out)
        self.assertIn("max_depth: 2", out)
        self.assertIn("filter: dev", out)

    def test_depth_out_of_range(self):
        code, _, err = run_cli("-p", "express", "-d", "0")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("max depth", err)

    def test_test_repo_file_not_found(self):
        code, _, err = run_cli("-p", "A", "-t", "-r", "nofile.txt")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("not found", err)


if __name__ == "__main__":
    unittest.main()
