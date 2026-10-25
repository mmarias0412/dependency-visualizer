"""Command-line interface of the dependency graph visualizer."""

import argparse
import sys
from typing import List, Optional

from config import (
    DEFAULT_MAX_DEPTH,
    Config,
    ConfigError,
    validate_depth,
    validate_filter,
    validate_package,
    validate_repo,
)
from registry import PackageInfo, RegistryError, get_direct_dependencies

EXIT_OK = 0
EXIT_FAILURE = 1
INDENT = "  "



def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all user-configurable options."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Visualize the dependency graph of an npm package.",
    )
    parser.add_argument(
        "-p", "--package", required=True,
        help="name of the package to analyze",
    )
    parser.add_argument(
        "-r", "--repo",
        help="repository URL, or path to a test repository file "
             "when --test-mode is set",
    )
    parser.add_argument(
        "-t", "--test-mode", action="store_true",
        help="read the dependency graph from a test repository file",
    )
    parser.add_argument(
        "-d", "--max-depth", type=int, default=DEFAULT_MAX_DEPTH,
        help="maximum depth of dependency analysis "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "-f", "--filter", default="", dest="filter_substring",
        help="skip packages whose name contains this substring",
    )
    return parser


def build_config(args: argparse.Namespace) -> Config:
    """Validate parsed arguments and build the Config object."""
    return Config(
        package=validate_package(args.package, args.test_mode),
        repo=validate_repo(args.repo, args.test_mode),
        test_mode=args.test_mode,
        max_depth=validate_depth(args.max_depth),
        filter_substring=validate_filter(args.filter_substring),
    )


def fetch_package_info(config: Config) -> PackageInfo:
    """Retrieve direct dependencies of the package from the repository."""
    if config.test_mode:
        raise RegistryError("test repository mode is not supported yet")
    return get_direct_dependencies(config.repo, config.package)


def format_dependencies(info: PackageInfo) -> List[str]:
    """Render direct dependencies as lines of text."""
    header = f"Direct dependencies of {info.name}@{info.version}:"
    if not info.dependencies:
        return [f"{header} none"]
    lines = [header]
    for name in sorted(info.dependencies):
        lines.append(f"{INDENT}{name}: {info.dependencies[name]}")
    return lines



def main(argv: Optional[List[str]] = None) -> int:
    """Parse options and print direct dependencies of the package."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config(args)
    except ConfigError as error:
        parser.error(str(error))
    try:
        info = fetch_package_info(config)
    except RegistryError as error:
        print(f"depviz: error: {error}", file=sys.stderr)
        return EXIT_FAILURE
    print("\n".join(format_dependencies(info)))
    return EXIT_OK

