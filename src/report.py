"""Text rendering of the dependency graph."""

from typing import List, Optional

from graph import Graph, find_cycles

NO_DEPENDENCIES = "-"
NO_DEPENDENTS = "(none)"
DEPTH_LIMIT_MARK = "(depth limit)"
FORWARD_ARROW = " -> "
REVERSE_ARROW = " <- "


def describe_dependencies(
    dependencies: Optional[List[str]], empty: str = NO_DEPENDENCIES
) -> str:
    """Describe the packages related to one package in a single line."""
    if dependencies is None:
        return DEPTH_LIMIT_MARK
    if not dependencies:
        return empty
    return ", ".join(dependencies)


def format_cycles(
    cycles: List[List[str]], arrow: str = FORWARD_ARROW
) -> List[str]:
    """Render found cycles, one per line."""
    if not cycles:
        return ["Cycles: none"]
    return [f"Cycle: {arrow.join(cycle)}" for cycle in cycles]


def format_graph(graph: Graph, max_depth: int) -> List[str]:
    """Render the graph in BFS order followed by a cycle report."""
    lines = [f"Dependency graph of {graph.root} (max depth {max_depth}):"]
    for name, dependencies in graph.edges.items():
        lines.append(f"{name}: {describe_dependencies(dependencies)}")
    lines.append(f"Packages: {len(graph.edges)}")
    lines.extend(format_cycles(find_cycles(graph)))
    return lines


def format_reverse_graph(graph: Graph, max_depth: int) -> List[str]:
    """Render the packages that depend on the root package."""
    lines = [f"Reverse dependencies of {graph.root} (max depth {max_depth}):"]
    for name, dependents in graph.edges.items():
        text = describe_dependencies(dependents, NO_DEPENDENTS)
        lines.append(f"{name}{REVERSE_ARROW}{text}")
    lines.append(_summarize_dependents(graph))
    lines.extend(format_cycles(find_cycles(graph), REVERSE_ARROW))
    return lines


def _summarize_dependents(graph: Graph) -> str:
    """Summarize all packages found to depend on the root package."""
    dependents = [name for name in graph.edges if name != graph.root]
    prefix = f"Packages that depend on {graph.root}"
    if not dependents:
        return f"{prefix}: none"
    return f"{prefix} ({len(dependents)}): {', '.join(dependents)}"
