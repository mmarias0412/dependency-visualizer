"""End-to-end scenarios on the bundled test repositories."""

import unittest

from helpers import example, run_cli

FAILURE_CODE = 1
USAGE_ERROR_CODE = 2


def run_example(name, *options):
    """Run the CLI in test mode on a bundled repository."""
    return run_cli("-t", "-r", example(name), *options)


def run_text(name, *options):
    """Run the CLI on a bundled repository with plain text output."""
    return run_example(name, "--format", "text", *options)


class ScenarioTests(unittest.TestCase):
    """Typical cases of working with a test repository."""

    def test_diamond(self):
        code, out, _ = run_text("diamond.txt", "-p", "A", "-d", "5")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            [
                "Dependency graph of A (max depth 5):",
                "A: B, C",
                "B: D",
                "C: D",
                "D: -",
                "Packages: 4",
                "Cycles: none",
            ],
        )

    def test_cycle(self):
        code, out, _ = run_text("cycle.txt", "-p", "A")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines()[1:],
            ["A: B", "B: C", "C: A", "Packages: 3",
             "Cycle: A -> B -> C -> A"],
        )

    def test_depth_limit(self):
        code, out, _ = run_text("chain.txt", "-p", "A", "-d", "2")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines()[1:],
            ["A: B", "B: C", "C: (depth limit)", "Packages: 3",
             "Cycles: none"],
        )

    def test_default_depth_is_three(self):
        _, out, _ = run_text("large.txt", "-p", "A")
        self.assertIn("max depth 3", out)
        self.assertIn("K: (depth limit)", out)
        self.assertNotIn("L:", out)

    def test_filter_removes_package_and_its_edges(self):
        _, out, _ = run_text("large.txt", "-p", "A", "-d", "5", "-f", "F")
        lines = out.splitlines()
        self.assertIn("B: E", lines)
        self.assertIn("C: G", lines)
        self.assertFalse(any(line.startswith("F:") for line in lines))

    def test_unreachable_packages_are_not_shown(self):
        _, out, _ = run_text("large.txt", "-p", "A", "-d", "5")
        self.assertNotIn("M:", out)
        self.assertNotIn("N:", out)

    def test_cycle_that_is_not_reachable_from_default_root(self):
        _, out, _ = run_text("large.txt", "-p", "M")
        self.assertIn("Cycle: M -> N -> M", out)

    def test_package_missing_from_test_repository(self):
        code, _, err = run_text("diamond.txt", "-p", "Z")
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("'Z' not found in test repository", err)


class ReverseScenarioTests(unittest.TestCase):
    """Reverse dependencies of packages in a test repository."""

    def test_shared_dependency(self):
        code, out, _ = run_text(
            "diamond.txt", "-p", "D", "-R", "-d", "5"
        )
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            [
                "Reverse dependencies of D (max depth 5):",
                "D <- B, C",
                "B <- A",
                "C <- A",
                "A <- (none)",
                "Packages that depend on D (3): B, C, A",
                "Cycles: none",
            ],
        )

    def test_package_nobody_depends_on(self):
        _, out, _ = run_text("diamond.txt", "-p", "A", "-R")
        self.assertEqual(
            out.splitlines()[1:],
            ["A <- (none)", "Packages that depend on A: none",
             "Cycles: none"],
        )

    def test_cycle(self):
        _, out, _ = run_text("cycle.txt", "-p", "A", "-R")
        self.assertEqual(
            out.splitlines()[1:],
            ["A <- C", "C <- B", "B <- A",
             "Packages that depend on A (2): C, B",
             "Cycle: A <- C <- B <- A"],
        )

    def test_depth_limit(self):
        _, out, _ = run_text("large.txt", "-p", "J", "-R", "-d", "2")
        lines = out.splitlines()
        self.assertIn("J <- F, G", lines)
        self.assertIn("B <- (depth limit)", lines)
        self.assertIn("Packages that depend on J (5): F, G, B, C, D", lines)

    def test_filter_skips_dependents(self):
        _, out, _ = run_text(
            "large.txt", "-p", "K", "-R", "-d", "5", "-f", "H"
        )
        lines = out.splitlines()
        self.assertIn("K <- J", lines)
        self.assertFalse(any(line.startswith("H") for line in lines))

    def test_cycles_through_root(self):
        _, out, _ = run_text("large.txt", "-p", "J", "-R", "-d", "5")
        self.assertIn("Cycle: A <- G <- C <- A", out)
        self.assertIn("Cycle: A <- G <- D <- A", out)

    def test_package_missing_from_test_repository(self):
        code, _, err = run_text("diamond.txt", "-p", "Z", "-R")
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("'Z' not found in test repository", err)


class PlantumlScenarioTests(unittest.TestCase):
    """PlantUML output on the bundled test repositories."""

    def test_diamond(self):
        code, out, _ = run_example("diamond.txt", "-p", "A", "-d", "5")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            [
                "@startuml",
                "title Dependency graph of A (max depth 5)",
                "skinparam rectangle {",
                "  BackgroundColor White",
                "  BackgroundColor<<root>> LightBlue",
                "  BackgroundColor<<limit>> LightGray",
                "}",
                'rectangle "A" as p0 <<root>>',
                'rectangle "B" as p1',
                'rectangle "C" as p2',
                'rectangle "D" as p3',
                "p0 --> p1",
                "p0 --> p2",
                "p1 --> p3",
                "p2 --> p3",
                "@enduml",
            ],
        )

    def test_cycle_closes_with_an_arrow_back(self):
        _, out, _ = run_example("cycle.txt", "-p", "A")
        self.assertIn("p2 --> p0", out.splitlines())

    def test_depth_limit_is_marked(self):
        _, out, _ = run_example("chain.txt", "-p", "A", "-d", "2")
        lines = out.splitlines()
        self.assertIn('rectangle "C" as p2 <<limit>>', lines)
        self.assertIn("legend right", lines)

    def test_reverse_arrows_still_point_to_dependencies(self):
        _, out, _ = run_example("diamond.txt", "-p", "D", "-R", "-d", "5")
        lines = out.splitlines()
        self.assertIn("title Reverse dependencies of D (max depth 5)", lines)
        self.assertIn("p1 --> p0", lines)
        self.assertIn("p3 --> p1", lines)

    def test_filter_removes_package(self):
        _, out, _ = run_example(
            "large.txt", "-p", "A", "-d", "5", "-f", "F"
        )
        self.assertNotIn('rectangle "F"', out)

    def test_unknown_format_is_rejected(self):
        code, _, err = run_example("diamond.txt", "-p", "A", "--format", "x")
        self.assertEqual(code, USAGE_ERROR_CODE)
        self.assertIn("--format", err)


if __name__ == "__main__":
    unittest.main()
