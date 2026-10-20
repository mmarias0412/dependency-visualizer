"""Configuration model and validation of user-supplied parameters."""

import os
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

DEFAULT_REPO_URL = "https://registry.npmjs.org"
DEFAULT_MAX_DEPTH = 3
MIN_DEPTH = 1
MAX_DEPTH = 100
MAX_NAME_LENGTH = 214
URL_SCHEMES = ("http", "https")
NPM_NAME_RE = re.compile(
    r"^(@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*$"
)
TEST_NAME_RE = re.compile(r"^[A-Z]+$")


class ConfigError(ValueError):
    """Raised when a user-supplied parameter is invalid."""


@dataclass(frozen=True)
class Config:
    """Validated parameters of the application."""

    package: str
    repo: str
    test_mode: bool
    max_depth: int
    filter_substring: str


def validate_package(name: str, test_mode: bool) -> str:
    """Check the package name against npm rules or test-repo rules."""
    if not name:
        raise ConfigError("package name must not be empty")
    if test_mode:
        if not TEST_NAME_RE.match(name):
            raise ConfigError(
                f"test package name must consist of capital Latin "
                f"letters, got '{name}'"
            )
        return name
    if len(name) > MAX_NAME_LENGTH:
        raise ConfigError(
            f"package name is longer than {MAX_NAME_LENGTH} characters"
        )
    if not NPM_NAME_RE.match(name):
        raise ConfigError(f"'{name}' is not a valid npm package name")
    return name


def validate_repo(repo: Optional[str], test_mode: bool) -> str:
    """Check that repo is an http(s) URL or an existing test file."""
    if test_mode:
        return _validate_repo_file(repo)
    if repo is None:
        return DEFAULT_REPO_URL
    parsed = urlparse(repo)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ConfigError(
            f"repository URL must start with http:// or https://, "
            f"got '{repo}'"
        )
    return repo


def _validate_repo_file(path: Optional[str]) -> str:
    """Check that the test repository path points to a readable file."""
    if not path:
        raise ConfigError("test mode requires --repo with a file path")
    if not os.path.isfile(path):
        raise ConfigError(f"test repository file not found: '{path}'")
    if not os.access(path, os.R_OK):
        raise ConfigError(f"test repository file is not readable: '{path}'")
    return path


def validate_depth(depth: int) -> int:
    """Check that the maximum analysis depth is within allowed bounds."""
    if depth < MIN_DEPTH or depth > MAX_DEPTH:
        raise ConfigError(
            f"max depth must be between {MIN_DEPTH} and {MAX_DEPTH}, "
            f"got {depth}"
        )
    return depth


def validate_filter(substring: str) -> str:
    """Check that the filter substring has no whitespace characters."""
    if any(char.isspace() for char in substring):
        raise ConfigError("filter substring must not contain whitespace")
    return substring
