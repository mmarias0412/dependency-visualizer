"""Tests for reading test repository files."""

import os
import tempfile
import unittest

from file_repo import (
    FileRepoError,
    load_repo,
    make_file_provider,
    parse_repo,
)


class ParseTests(unittest.TestCase):
    """Parsing of the test repository format."""

    def test_valid_description(self):
        lines = ["A: B, C", "# comment", "", "B: C  # trailing", "C:"]
        self.assertEqual(
            parse_repo(lines),
            {"A": ["B", "C"], "B": ["C"], "C": []},
        )

    def test_duplicate_dependencies_are_merged(self):
        self.assertEqual(parse_repo(["A: B B C"]), {"A": ["B", "C"]})

    def check_error(self, lines, expected):
        with self.assertRaises(FileRepoError) as context:
            parse_repo(lines)
        self.assertIn(expected, str(context.exception))

    def test_missing_separator(self):
        self.check_error(["A B"], "line 1: expected")

    def test_lowercase_package_name(self):
        self.check_error(["A: B", "b: C"], "line 2: 'b'")

    def test_lowercase_dependency_name(self):
        self.check_error(["A: B c"], "'c' is not a valid package name")

    def test_empty_package_name(self):
        self.check_error([": B"], "line 1: ''")

    def test_duplicate_declaration(self):
        self.check_error(["A: B", "A: C"], "declared twice")


class FileTests(unittest.TestCase):
    """Loading of files and construction of the provider."""

    def write_repo(self, directory, text):
        path = os.path.join(directory, "repo.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def test_missing_file(self):
        with self.assertRaises(FileRepoError) as context:
            load_repo("no_such_file.txt")
        self.assertIn("cannot read", str(context.exception))

    def test_provider_returns_sorted_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_repo(directory, "A: C B\nB:\nC:\n")
            provider = make_file_provider(path, "A")
        self.assertEqual(provider("A"), ["B", "C"])

    def test_undeclared_package_has_no_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_repo(directory, "A: Z\n")
            provider = make_file_provider(path, "A")
        self.assertEqual(provider("Z"), [])

    def test_root_must_be_declared(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_repo(directory, "A: B\n")
            with self.assertRaises(FileRepoError) as context:
                make_file_provider(path, "X")
        self.assertIn("'X' not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
