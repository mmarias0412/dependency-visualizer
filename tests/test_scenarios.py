"""End-to-end scenarios on the bundled test repositories."""

import unittest

from helpers import example, run_cli

FAILURE_CODE = 1


def run_example(name, *options):
    """Run the CLI in test mode on a bundled repository."""
    return run_cli("-t", "-r", example(name), *options)


class ScenarioTests(unittest.TestCase):
    """Typical cases of working with a test repository."""

    def test_diamond(self):
        code, out, _ = run_example("diamond.txt", "-p", "A", "-d", "5")
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
        code, out, _ = run_example("cycle.txt", "-p", "A")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines()[1:],
            ["A: B", "B: C", "C: A", "Packages: 3",
             "Cycle: A -> B -> C -> A"],
        )

    def test_depth_limit(self):
        code, out, _ = run_example("chain.txt", "-p", "A", "-d", "2")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines()[1:],
            ["A: B", "B: C", "C: (depth limit)", "Packages: 3",
             "Cycles: none"],
        )

    def test_default_depth_is_three(self):
        _, out, _ = run_example("large.txt", "-p", "A")
        self.assertIn("max depth 3", out)
        self.assertIn("K: (depth limit)", out)
        self.assertNotIn("L:", out)

    def test_filter_removes_package_and_its_edges(self):
        _, out, _ = run_example("large.txt", "-p", "A", "-d", "5", "-f", "F")
        lines = out.splitlines()
        self.assertIn("B: E", lines)
        self.assertIn("C: G", lines)
        self.assertFalse(any(line.startswith("F:") for line in lines))

    def test_unreachable_packages_are_not_shown(self):
        _, out, _ = run_example("large.txt", "-p", "A", "-d", "5")
        self.assertNotIn("M:", out)
        self.assertNotIn("N:", out)

    def test_cycle_that_is_not_reachable_from_default_root(self):
        _, out, _ = run_example("large.txt", "-p", "M")
        self.assertIn("Cycle: M -> N -> M", out)

    def test_package_missing_from_test_repository(self):
        code, _, err = run_example("diamond.txt", "-p", "Z")
        self.assertEqual(code, FAILURE_CODE)
        self.assertIn("'Z' not found in test repository", err)


if __name__ == "__main__":
    unittest.main()
