"""Tests for collecting direct dependencies from a registry."""

import json
import unittest

from helpers import MockRegistry, run_cli
from registry import build_manifest_url

HTTP_OK = 200
HTTP_SERVER_ERROR = 500
FAILURE_CODE = 1
UNREACHABLE_REPO = "http://127.0.0.1:1"


def manifest(version="4.0.0", **extra):
    """Encode a package manifest as a JSON response body."""
    return json.dumps({"version": version, **extra}).encode("utf-8")


class UrlTests(unittest.TestCase):
    """Building of manifest URLs."""

    def test_plain_package(self):
        url = build_manifest_url("https://registry.npmjs.org/", "express")
        self.assertEqual(url, "https://registry.npmjs.org/express/latest")

    def test_scoped_package(self):
        url = build_manifest_url("http://host", "@babel/core")
        self.assertEqual(url, "http://host/@babel%2Fcore/latest")


class DependenciesTests(unittest.TestCase):
    """Successful retrieval of direct dependencies."""

    def test_prints_sorted_dependencies(self):
        body = manifest(dependencies={"b": "^1.0.0", "a": "~2.1.0"})
        with MockRegistry({"/express/latest": (HTTP_OK, body)}) as repo:
            code, out, _ = run_cli("-p", "express", "-r", repo)
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            ["Direct dependencies of express@4.0.0:",
             "  a: ~2.1.0", "  b: ^1.0.0"],
        )

    def test_no_dependencies(self):
        with MockRegistry({"/leaf/latest": (HTTP_OK, manifest())}) as repo:
            code, out, _ = run_cli("-p", "leaf", "-r", repo)
        self.assertEqual(code, 0)
        self.assertIn("leaf@4.0.0: none", out)

    def test_scoped_package(self):
        routes = {"/@babel%2Fcore/latest": (HTTP_OK, manifest("7.0.0"))}
        with MockRegistry(routes) as repo:
            code, out, _ = run_cli("-p", "@babel/core", "-r", repo)
        self.assertEqual(code, 0)
        self.assertIn("@babel/core@7.0.0", out)


class ErrorTests(unittest.TestCase):
    """Failures while talking to the registry."""

    def check_failure(self, routes, expected):
        with MockRegistry(routes) as repo:
            code, _, err = run_cli("-p", "express", "-r", repo)
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn(expected, err)

    def test_package_not_found(self):
        self.check_failure({}, "not found in repository")

    def test_server_error(self):
        routes = {"/express/latest": (HTTP_SERVER_ERROR, b"")}
        self.check_failure(routes, "HTTP status 500")

    def test_invalid_json(self):
        routes = {"/express/latest": (HTTP_OK, b"<html>")}
        self.check_failure(routes, "invalid JSON")

    def test_missing_version(self):
        routes = {"/express/latest": (HTTP_OK, b"{}")}
        self.check_failure(routes, "no version")

    def test_malformed_dependencies(self):
        body = manifest(dependencies=["a"])
        self.check_failure({"/express/latest": (HTTP_OK, body)},
                           "malformed dependencies")

    def test_repository_unreachable(self):
        code, _, err = run_cli("-p", "express", "-r", UNREACHABLE_REPO)
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("cannot connect", err)

    def test_test_mode_not_supported_yet(self):
        code, _, err = run_cli("-p", "A", "-t", "-r", __file__)
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("not supported yet", err)


if __name__ == "__main__":
    unittest.main()
