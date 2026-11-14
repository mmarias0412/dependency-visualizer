"""Tests for the PlantUML renderer."""

import unittest

from graph import Graph, build_graph
from plantuml import format_plantuml

NO_FILTER = ""
DEEP = 5


def render(repo, root="A", depth=DEEP, reverse=False):
    """Build a graph from a dict and render it as PlantUML."""
    graph = build_graph(
        root, lambda name: sorted(repo.get(name, [])), depth, NO_FILTER
    )
    return format_plantuml(graph, depth, reverse)


class StructureTests(unittest.TestCase):
    """General shape of the generated diagram."""

    def test_starts_and_ends_with_markers(self):
        lines = render({"A": ["B"]})
        self.assertEqual(lines[0], "@startuml")
        self.assertEqual(lines[-1], "@enduml")

    def test_title_mentions_root_and_depth(self):
        lines = render({"A": ["B"]}, depth=3)
        self.assertIn("title Dependency graph of A (max depth 3)", lines)

    def test_single_package(self):
        lines = render({})
        self.assertIn('rectangle "A" as p0 <<root>>', lines)
        self.assertFalse(any("-->" in line for line in lines))

    def test_aliases_follow_bfs_order(self):
        lines = render({"A": ["B", "C"], "B": ["D"], "C": ["E"]})
        declared = [line for line in lines if line.startswith("rectangle")]
        names = [line.split('"')[1] for line in declared]
        self.assertEqual(names, ["A", "B", "C", "D", "E"])
        self.assertEqual(declared[3], 'rectangle "D" as p3')

    def test_every_edge_becomes_an_arrow(self):
        lines = render({"A": ["B", "C"], "B": ["C"]})
        arrows = [line for line in lines if "-->" in line]
        self.assertEqual(arrows, ["p0 --> p1", "p0 --> p2", "p1 --> p2"])


class MarkingTests(unittest.TestCase):
    """Special marks for the root, cycles and the depth limit."""

    def test_depth_limit_node_and_legend(self):
        lines = render({"A": ["B"], "B": ["C"]}, depth=1)
        self.assertIn('rectangle "B" as p1 <<limit>>', lines)
        self.assertIn("legend right", lines)

    def test_no_legend_without_depth_limit(self):
        lines = render({"A": ["B"]})
        self.assertNotIn("legend right", lines)

    def test_cycle_arrow_points_back(self):
        lines = render({"A": ["B"], "B": ["A"]})
        self.assertIn("p1 --> p0", lines)

    def test_self_dependency(self):
        lines = render({"A": ["A"]})
        self.assertIn("p0 --> p0", lines)

    def test_scoped_and_dashed_names_are_quoted(self):
        graph = Graph("@scope/pkg", {"@scope/pkg": ["body-parser"],
                                     "body-parser": []})
        lines = format_plantuml(graph, DEEP)
        self.assertIn('rectangle "@scope/pkg" as p0 <<root>>', lines)
        self.assertIn('rectangle "body-parser" as p1', lines)


class ReverseTests(unittest.TestCase):
    """Reverse mode keeps arrows pointing at dependencies."""

    def test_arrows_are_flipped(self):
        dependents = {"D": ["B", "C"], "B": ["A"], "C": ["A"]}
        lines = render(dependents, root="D", reverse=True)
        arrows = [line for line in lines if "-->" in line]
        self.assertEqual(
            arrows, ["p1 --> p0", "p2 --> p0", "p3 --> p1", "p3 --> p2"]
        )

    def test_title(self):
        lines = render({"D": ["B"]}, root="D", reverse=True)
        self.assertIn(
            "title Reverse dependencies of D (max depth 5)", lines
        )


if __name__ == "__main__":
    unittest.main()
