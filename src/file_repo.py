"""Test repository: a dependency graph described by a text file.

Each line has the form ``PACKAGE: DEPENDENCY DEPENDENCY ...``. Names are
capital Latin letters, dependencies are separated by spaces or commas,
blank lines and text after ``#`` are ignored.
"""

from typing import Dict, List, Tuple

from config import TEST_NAME_RE
from errors import RepositoryError
from graph import DependencyProvider

COMMENT_MARK = "#"
SEPARATOR = ":"
FIRST_LINE_NUMBER = 1

TestRepo = Dict[str, List[str]]


class FileRepoError(RepositoryError):
    """Raised when a test repository file is unreadable or malformed."""


def load_repo(path: str) -> TestRepo:
    """Read and parse a test repository file."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise FileRepoError(
            f"cannot read test repository '{path}': {error}"
        ) from error
    return parse_repo(lines)


def parse_repo(lines: List[str]) -> TestRepo:
    """Parse the lines of a test repository description."""
    repo: TestRepo = {}
    for number, raw in enumerate(lines, start=FIRST_LINE_NUMBER):
        line = raw.partition(COMMENT_MARK)[0].strip()
        if not line:
            continue
        name, dependencies = _parse_line(line, number)
        if name in repo:
            raise FileRepoError(
                f"line {number}: package '{name}' is declared twice"
            )
        repo[name] = dependencies
    return repo


def _parse_line(line: str, number: int) -> Tuple[str, List[str]]:
    """Split a line into a package name and its dependencies."""
    head, separator, tail = line.partition(SEPARATOR)
    if not separator:
        raise FileRepoError(
            f"line {number}: expected 'PACKAGE: DEPENDENCIES'"
        )
    name = head.strip()
    dependencies = list(dict.fromkeys(tail.replace(",", " ").split()))
    for item in [name, *dependencies]:
        if not TEST_NAME_RE.match(item):
            raise FileRepoError(
                f"line {number}: '{item}' is not a valid package name "
                f"(capital Latin letters only)"
            )
    return name, dependencies


def make_file_provider(path: str, root: str) -> DependencyProvider:
    """Create a dependency provider backed by a test repository file."""
    repo = load_repo(path)
    if root not in repo:
        raise _not_found(root)

    def provider(name: str) -> List[str]:
        """Return direct dependencies; undeclared packages have none."""
        return sorted(repo.get(name, []))

    return provider


def make_reverse_provider(path: str, root: str) -> DependencyProvider:
    """Create a provider that lists the packages depending on a package."""
    repo = load_repo(path)
    dependents: TestRepo = {}
    for name, dependencies in repo.items():
        for dependency in dependencies:
            dependents.setdefault(dependency, []).append(name)
    if root not in repo and root not in dependents:
        raise _not_found(root)

    def provider(name: str) -> List[str]:
        """Return sorted names of the direct dependents of a package."""
        return sorted(dependents.get(name, []))

    return provider


def _not_found(root: str) -> FileRepoError:
    """Build the error for a package missing from the test repository."""
    return FileRepoError(f"package '{root}' not found in test repository")
