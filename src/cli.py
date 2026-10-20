"""Command-line interface of the dependency graph visualizer."""

import argparse
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

EXIT_OK = 0


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


def format_config(config: Config) -> List[str]:
    """Render configuration as a list of 'key: value' lines."""
    return [
        f"package: {config.package}",
        f"repo: {config.repo}",
        f"test_mode: {str(config.test_mode).lower()}",
        f"max_depth: {config.max_depth}",
        f"filter: {config.filter_substring}",
    ]


def main(argv: Optional[List[str]] = None) -> int:
    """Parse options, validate them and print them as key-value pairs."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config(args)
    except ConfigError as error:
        parser.error(str(error))
    print("\n".join(format_config(config)))
    return EXIT_OK
