"""Text rendering of the dependency graph."""

from typing import List, Optional

from graph import Graph, find_cycles

NO_DEPENDENCIES = "-"
DEPTH_LIMIT_MARK = "(depth limit)"
CYCLE_ARROW = " -> "


def describe_dependencies(dependencies: Optional[List[str]]) -> str:
    """Describe the dependencies of one package in a single line."""
    if dependencies is None:
        return DEPTH_LIMIT_MARK
    if not dependencies:
        return NO_DEPENDENCIES
    return ", ".join(dependencies)


def format_cycles(cycles: List[List[str]]) -> List[str]:
    """Render found cycles, one per line."""
    if not cycles:
        return ["Cycles: none"]
    return [f"Cycle: {CYCLE_ARROW.join(cycle)}" for cycle in cycles]


def format_graph(graph: Graph, max_depth: int) -> List[str]:
    """Render the graph in BFS order followed by a cycle report."""
    lines = [f"Dependency graph of {graph.root} (max depth {max_depth}):"]
    for name, dependencies in graph.edges.items():
        lines.append(f"{name}: {describe_dependencies(dependencies)}")
    lines.append(f"Packages: {len(graph.edges)}")
    lines.extend(format_cycles(find_cycles(graph)))
    return lines
