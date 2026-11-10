"""Tests for reading test repository files."""

import os
import tempfile
import unittest

from file_repo import (
    FileRepoError,
    load_repo,
    make_file_provider,
    make_reverse_provider,
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


class ReverseTests(unittest.TestCase):
    """Provider of the packages that depend on a package."""

    def provider_for(self, text, root):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "repo.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            return make_reverse_provider(path, root)

    def test_lists_sorted_dependents(self):
        provider = self.provider_for("A: C\nB: C D\nC:\n", "C")
        self.assertEqual(provider("C"), ["A", "B"])
        self.assertEqual(provider("D"), ["B"])

    def test_package_nobody_depends_on(self):
        provider = self.provider_for("A: B\n", "A")
        self.assertEqual(provider("A"), [])

    def test_package_known_only_as_dependency(self):
        provider = self.provider_for("A: Z\n", "Z")
        self.assertEqual(provider("Z"), ["A"])

    def test_self_dependency_is_listed(self):
        provider = self.provider_for("A: A\n", "A")
        self.assertEqual(provider("A"), ["A"])

    def test_unknown_package(self):
        with self.assertRaises(FileRepoError) as context:
            self.provider_for("A: B\n", "X")
        self.assertIn("'X' not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
