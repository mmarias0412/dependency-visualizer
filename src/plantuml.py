"""Rendering of the dependency graph in the PlantUML language."""

from typing import Dict, List

from graph import Graph

START_MARK = "@startuml"
END_MARK = "@enduml"
ARROW = "-->"
ROOT_STEREOTYPE = "<<root>>"
LIMIT_STEREOTYPE = "<<limit>>"
STYLE = [
    "skinparam rectangle {",
    "  BackgroundColor White",
    "  BackgroundColor<<root>> LightBlue",
    "  BackgroundColor<<limit>> LightGray",
    "}",
]
LEGEND = [
    "legend right",
    "  Gray: depth limit reached, dependencies are not expanded",
    "endlegend",
]


def format_plantuml(
    graph: Graph, max_depth: int, reverse: bool = False
) -> List[str]:
    """Describe the graph as a PlantUML diagram.

    An arrow always points from a package to a package it depends on.
    In reverse mode the traversal edges are flipped to keep that meaning.
    """
    aliases = _assign_aliases(graph)
    lines = [START_MARK, f"title {_title(graph, max_depth, reverse)}"]
    lines.extend(STYLE)
    if any(targets is None for targets in graph.edges.values()):
        lines.extend(LEGEND)
    lines.extend(_declare_nodes(graph, aliases))
    lines.extend(_declare_arrows(graph, aliases, reverse))
    lines.append(END_MARK)
    return lines


def _title(graph: Graph, max_depth: int, reverse: bool) -> str:
    """Build the diagram title."""
    kind = "Reverse dependencies" if reverse else "Dependency graph"
    return f"{kind} of {graph.root} (max depth {max_depth})"


def _assign_aliases(graph: Graph) -> Dict[str, str]:
    """Give every package a short identifier valid in PlantUML."""
    return {name: f"p{index}" for index, name in enumerate(graph.edges)}


def _declare_nodes(graph: Graph, aliases: Dict[str, str]) -> List[str]:
    """Declare one rectangle per package, in BFS order."""
    lines = []
    for name, targets in graph.edges.items():
        line = f'rectangle "{name}" as {aliases[name]}'
        if name == graph.root:
            line += f" {ROOT_STEREOTYPE}"
        elif targets is None:
            line += f" {LIMIT_STEREOTYPE}"
        lines.append(line)
    return lines


def _declare_arrows(
    graph: Graph, aliases: Dict[str, str], reverse: bool
) -> List[str]:
    """Declare one arrow per edge of the graph."""
    lines = []
    for name, targets in graph.edges.items():
        for target in targets or []:
            source, destination = (target, name) if reverse else (name, target)
            lines.append(f"{aliases[source]} {ARROW} {aliases[destination]}")
    return lines
