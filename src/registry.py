"""Retrieval of direct package dependencies from an npm registry."""

import http.client
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib.parse import quote

from errors import RepositoryError
from graph import DependencyProvider

REQUEST_TIMEOUT_SECONDS = 10
HTTP_NOT_FOUND = 404
LATEST_TAG = "latest"
DEPENDENCIES_FIELD = "dependencies"
USER_AGENT = "depviz"


class RegistryError(RepositoryError):
    """Raised when package data cannot be retrieved or understood."""


@dataclass(frozen=True)
class PackageInfo:
    """Name, version and direct dependencies of one package."""

    name: str
    version: str
    dependencies: Dict[str, str]


def build_manifest_url(repo: str, package: str) -> str:
    """Build the URL of the latest-version manifest of a package."""
    base = repo.rstrip("/")
    return f"{base}/{quote(package, safe='@')}/{LATEST_TAG}"


def fetch_json(url: str, package: str) -> Any:
    """Download a URL and decode its body as JSON."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        raise _http_error(error, package) from error
    except urllib.error.URLError as error:
        raise RegistryError(
            f"cannot connect to repository: {error.reason}"
        ) from error
    except (OSError, http.client.HTTPException) as error:
        raise RegistryError(f"network error: {error}") from error
    return _decode_json(body)


def _http_error(error: urllib.error.HTTPError, package: str) -> RegistryError:
    """Convert an HTTP error status into a RegistryError."""
    if error.code == HTTP_NOT_FOUND:
        return RegistryError(f"package '{package}' not found in repository")
    return RegistryError(f"repository returned HTTP status {error.code}")


def _decode_json(body: bytes) -> Any:
    """Decode a response body as UTF-8 JSON."""
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError as error:
        raise RegistryError("repository returned invalid JSON") from error


def parse_manifest(data: Any, package: str) -> PackageInfo:
    """Extract version and direct dependencies from a manifest."""
    if not isinstance(data, dict):
        raise RegistryError("repository returned unexpected data")
    version = data.get("version")
    if not isinstance(version, str) or not version:
        raise RegistryError("package manifest has no version")
    raw = data.get(DEPENDENCIES_FIELD, {})
    if not _is_string_mapping(raw):
        raise RegistryError("package manifest has malformed dependencies")
    return PackageInfo(package, version, dict(raw))


def _is_string_mapping(value: Any) -> bool:
    """Check that value is a dict with string keys and string values."""
    if not isinstance(value, dict):
        return False
    return all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in value.items()
    )


def get_direct_dependencies(repo: str, package: str) -> PackageInfo:
    """Fetch the direct dependencies of the latest package version."""
    url = build_manifest_url(repo, package)
    return parse_manifest(fetch_json(url, package), package)


def make_registry_provider(repo: str) -> DependencyProvider:
    """Create a dependency provider that queries an npm registry."""

    def provider(name: str) -> List[str]:
        """Return sorted names of direct dependencies of a package."""
        return sorted(get_direct_dependencies(repo, name).dependencies)

    return provider
