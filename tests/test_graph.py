"""Tests for BFS graph construction and cycle detection."""

import unittest

from graph import build_graph, find_cycles

NO_FILTER = ""
LARGE_DEPTH = 5


def provider_from(repo, calls=None):
    """Make a dependency provider that reads a dict and logs requests."""

    def provider(name):
        if calls is not None:
            calls.append(name)
        return sorted(repo.get(name, []))

    return provider


class BfsTests(unittest.TestCase):
    """Order, depth and visiting rules of the graph builder."""

    def test_diamond_edges(self):
        repo = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        graph = build_graph("A", provider_from(repo), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(
            graph.edges,
            {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []},
        )

    def test_breadth_first_order(self):
        repo = {"A": ["B", "C"], "B": ["D"], "C": ["E"]}
        graph = build_graph("A", provider_from(repo), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(list(graph.edges), ["A", "B", "C", "D", "E"])

    def test_each_package_requested_once(self):
        calls = []
        repo = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        build_graph("A", provider_from(repo, calls), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(calls, ["A", "B", "C", "D"])

    def test_package_without_dependencies(self):
        graph = build_graph("A", provider_from({}), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(graph.edges, {"A": []})

    def test_depth_one_lists_only_direct_dependencies(self):
        repo = {"A": ["B", "C"], "B": ["D"]}
        graph = build_graph("A", provider_from(repo), 1, NO_FILTER)
        self.assertEqual(graph.edges, {"A": ["B", "C"], "B": None, "C": None})

    def test_depth_limit_stops_chain(self):
        repo = {"A": ["B"], "B": ["C"], "C": ["D"]}
        graph = build_graph("A", provider_from(repo), 2, NO_FILTER)
        self.assertEqual(graph.edges, {"A": ["B"], "B": ["C"], "C": None})

    def test_depth_limit_does_not_request_deeper_packages(self):
        calls = []
        repo = {"A": ["B"], "B": ["C"], "C": ["D"]}
        build_graph("A", provider_from(repo, calls), 2, NO_FILTER)
        self.assertEqual(calls, ["A", "B"])

    def test_very_long_chain_within_maximum_depth(self):
        size = 150
        repo = {f"P{i}": [f"P{i + 1}"] for i in range(size)}
        graph = build_graph("P0", provider_from(repo), 100, NO_FILTER)
        self.assertEqual(len(graph.edges), 101)
        self.assertIsNone(graph.edges["P100"])


class FilterTests(unittest.TestCase):
    """Packages whose name contains the substring are skipped."""

    def test_filtered_dependency_is_removed(self):
        repo = {"app": ["lib-core", "lib-types", "util"]}
        graph = build_graph("app", provider_from(repo), 1, "types")
        self.assertEqual(graph.edges["app"], ["lib-core", "util"])
        self.assertNotIn("lib-types", graph.edges)

    def test_dependencies_of_filtered_package_are_not_visited(self):
        calls = []
        repo = {"A": ["B", "C"], "B": ["D"]}
        graph = build_graph("A", provider_from(repo, calls), 5, "B")
        self.assertEqual(graph.edges, {"A": ["C"], "C": []})
        self.assertEqual(calls, ["A", "C"])

    def test_empty_substring_filters_nothing(self):
        repo = {"A": ["B"]}
        graph = build_graph("A", provider_from(repo), 1, NO_FILTER)
        self.assertEqual(graph.edges["A"], ["B"])


class CycleTests(unittest.TestCase):
    """Cyclic dependencies must neither hang nor be lost."""

    def test_simple_cycle(self):
        repo = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_graph("A", provider_from(repo), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(list(graph.edges), ["A", "B", "C"])
        self.assertEqual(find_cycles(graph), [["A", "B", "C", "A"]])

    def test_self_dependency(self):
        graph = build_graph(
            "A", provider_from({"A": ["A"]}), LARGE_DEPTH, NO_FILTER
        )
        self.assertEqual(graph.edges, {"A": ["A"]})
        self.assertEqual(find_cycles(graph), [["A", "A"]])

    def test_cycle_not_through_root(self):
        repo = {"A": ["B"], "B": ["C"], "C": ["B"]}
        graph = build_graph("A", provider_from(repo), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(find_cycles(graph), [["B", "C", "B"]])

    def test_acyclic_graph_has_no_cycles(self):
        repo = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        graph = build_graph("A", provider_from(repo), LARGE_DEPTH, NO_FILTER)
        self.assertEqual(find_cycles(graph), [])


if __name__ == "__main__":
    unittest.main()
