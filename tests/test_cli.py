"""Tests for validation of command-line options."""

import unittest

from helpers import example, run_cli

USAGE_ERROR_CODE = 2


class CliTests(unittest.TestCase):
    """Usage errors reported by the command-line interface."""

    def test_missing_package(self):
        code, _, err = run_cli()
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("--package", err)

    def test_depth_out_of_range(self):
        code, _, err = run_cli("-p", "express", "-d", "0")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("max depth", err)

    def test_test_repo_file_not_found(self):
        code, _, err = run_cli("-p", "A", "-t", "-r", "nofile.txt")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("not found", err)

    def test_filter_excludes_analyzed_package(self):
        repo = example("diamond.txt")
        code, _, err = run_cli("-p", "A", "-t", "-r", repo, "-f", "A")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("excluded", err)

    def test_reverse_mode_requires_test_mode(self):
        code, _, err = run_cli("-p", "express", "--reverse")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("--test-mode", err)


if __name__ == "__main__":
    unittest.main()
