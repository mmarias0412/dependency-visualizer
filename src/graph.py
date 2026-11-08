"""Construction of the dependency graph with a recursive BFS."""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set

from config import matches_filter

ROOT_DEPTH = 0
DependencyProvider = Callable[[str], List[str]]
Edges = Dict[str, Optional[List[str]]]


@dataclass(frozen=True)
class Graph:
    """Dependency graph reachable from the root package.

    Edges are stored in BFS order. A package maps to the list of its
    direct dependencies, or to None when it was reached but not
    expanded because the maximum depth was exhausted.
    """

    root: str
    edges: Edges


class GraphBuilder:
    """Level-by-level graph construction implemented with recursion."""

    def __init__(
        self, provider: DependencyProvider, max_depth: int, substring: str
    ) -> None:
        self._provider = provider
        self._max_depth = max_depth
        self._substring = substring
        self._seen: Set[str] = set()
        self._edges: Edges = {}

    def run(self, root: str) -> Graph:
        """Build the graph that starts at the root package."""
        self._seen.add(root)
        self._walk_level([root], ROOT_DEPTH)
        return Graph(root, self._edges)

    def _walk_level(self, level: List[str], depth: int) -> None:
        """Process one BFS level, then recurse into the next one."""
        if not level:
            return
        next_level: List[str] = []
        for name in level:
            next_level.extend(self._process(name, depth))
        self._walk_level(next_level, depth + 1)

    def _process(self, name: str, depth: int) -> List[str]:
        """Expand one package and return its not yet seen dependencies."""
        if depth >= self._max_depth:
            self._edges[name] = None
            return []
        dependencies = self._visible_dependencies(name)
        self._edges[name] = dependencies
        return self._take_unseen(dependencies)

    def _visible_dependencies(self, name: str) -> List[str]:
        """Return direct dependencies that pass the name filter."""
        allowed = [
            dependency
            for dependency in self._provider(name)
            if not matches_filter(dependency, self._substring)
        ]
        return list(dict.fromkeys(allowed))

    def _take_unseen(self, dependencies: List[str]) -> List[str]:
        """Mark new packages as seen and return them."""
        fresh = []
        for dependency in dependencies:
            if dependency not in self._seen:
                self._seen.add(dependency)
                fresh.append(dependency)
        return fresh


def build_graph(
    root: str, provider: DependencyProvider, max_depth: int, substring: str
) -> Graph:
    """Build the dependency graph of root up to max_depth levels."""
    return GraphBuilder(provider, max_depth, substring).run(root)


def find_cycles(graph: Graph) -> List[List[str]]:
    """Find one cycle for every back edge met by a depth-first walk."""
    cycles: List[List[str]] = []
    path = [graph.root]
    done: Set[str] = set()
    stack = [iter(graph.edges.get(graph.root) or [])]
    while stack:
        target = next(stack[-1], None)
        if target is None:
            done.add(path.pop())
            stack.pop()
        elif target in path:
            cycles.append(path[path.index(target):] + [target])
        elif target not in done:
            path.append(target)
            stack.append(iter(graph.edges.get(target) or []))
    return cycles
