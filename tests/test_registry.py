"""Tests for collecting dependencies from a registry."""

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


def ok(body):
    """Pair a body with the HTTP 200 status."""
    return HTTP_OK, body


class UrlTests(unittest.TestCase):
    """Building of manifest URLs."""

    def test_plain_package(self):
        url = build_manifest_url("https://registry.npmjs.org/", "express")
        self.assertEqual(url, "https://registry.npmjs.org/express/latest")

    def test_scoped_package(self):
        url = build_manifest_url("http://host", "@babel/core")
        self.assertEqual(url, "http://host/@babel%2Fcore/latest")


class GraphTests(unittest.TestCase):
    """Graphs assembled from registry responses."""

    def run_graph(self, routes, *options):
        with MockRegistry(routes) as repo:
            return run_cli("-r", repo, *options)

    def test_transitive_dependencies(self):
        routes = {
            "/a/latest": ok(manifest(dependencies={"b": "^1", "c": "^1"})),
            "/b/latest": ok(manifest(dependencies={"c": "^1"})),
            "/c/latest": ok(manifest()),
        }
        code, out, _ = self.run_graph(routes, "-p", "a")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            [
                "Dependency graph of a (max depth 3):",
                "a: b, c",
                "b: c",
                "c: -",
                "Packages: 3",
                "Cycles: none",
            ],
        )

    def test_depth_one_does_not_query_dependencies(self):
        routes = {
            "/a/latest": ok(manifest(dependencies={"b": "^1"})),
        }
        code, out, _ = self.run_graph(routes, "-p", "a", "-d", "1")
        self.assertEqual(code, 0)
        self.assertIn("b: (depth limit)", out)

    def test_cyclic_registry(self):
        routes = {
            "/a/latest": ok(manifest(dependencies={"b": "^1"})),
            "/b/latest": ok(manifest(dependencies={"a": "^1"})),
        }
        code, out, _ = self.run_graph(routes, "-p", "a")
        self.assertEqual(code, 0)
        self.assertIn("Cycle: a -> b -> a", out)

    def test_filter(self):
        routes = {
            "/a/latest": ok(
                manifest(dependencies={"b": "^1", "types-b": "^1"})
            ),
            "/b/latest": ok(manifest()),
        }
        _, out, _ = self.run_graph(routes, "-p", "a", "-f", "types")
        self.assertIn("a: b", out.splitlines())
        self.assertNotIn("types-b:", out)

    def test_scoped_package(self):
        routes = {"/@babel%2Fcore/latest": ok(manifest("7.0.0"))}
        code, out, _ = self.run_graph(routes, "-p", "@babel/core")
        self.assertEqual(code, 0)
        self.assertIn("@babel/core: -", out)

    def test_missing_transitive_dependency(self):
        routes = {"/a/latest": ok(manifest(dependencies={"b": "^1"}))}
        code, _, err = self.run_graph(routes, "-p", "a")
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("package 'b' not found", err)


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
        routes = {"/express/latest": ok(b"<html>")}
        self.check_failure(routes, "invalid JSON")

    def test_missing_version(self):
        routes = {"/express/latest": ok(b"{}")}
        self.check_failure(routes, "no version")

    def test_malformed_dependencies(self):
        body = manifest(dependencies=["a"])
        self.check_failure({"/express/latest": ok(body)},
                           "malformed dependencies")

    def test_repository_unreachable(self):
        code, _, err = run_cli("-p", "express", "-r", UNREACHABLE_REPO)
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("cannot connect", err)


if __name__ == "__main__":
    unittest.main()
