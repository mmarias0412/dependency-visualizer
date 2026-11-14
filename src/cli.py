"""Command-line interface of the dependency graph visualizer."""

import argparse
import sys
from typing import List, Optional

from config import (
    DEFAULT_MAX_DEPTH,
    FORMAT_PLANTUML,
    FORMAT_TEXT,
    OUTPUT_FORMATS,
    Config,
    ConfigError,
    validate_depth,
    validate_filter,
    validate_package,
    validate_package_not_filtered,
    validate_repo,
    validate_reverse,
)
from errors import RepositoryError
from file_repo import make_file_provider, make_reverse_provider
from graph import DependencyProvider, Graph, build_graph
from plantuml import format_plantuml
from registry import make_registry_provider
from report import format_graph, format_reverse_graph

EXIT_OK = 0
EXIT_FAILURE = 1


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
    parser.add_argument(
        "-R", "--reverse", action="store_true",
        help="show the packages that depend on the package "
             "(needs --test-mode)",
    )
    parser.add_argument(
        "--format", choices=OUTPUT_FORMATS, default=FORMAT_PLANTUML,
        dest="output_format",
        help="output format: PlantUML diagram or plain text "
             "(default: %(default)s)",
    )
    return parser


def build_config(args: argparse.Namespace) -> Config:
    """Validate parsed arguments and build the Config object."""
    config = Config(
        package=validate_package(args.package, args.test_mode),
        repo=validate_repo(args.repo, args.test_mode),
        test_mode=args.test_mode,
        max_depth=validate_depth(args.max_depth),
        filter_substring=validate_filter(args.filter_substring),
        reverse=validate_reverse(args.reverse, args.test_mode),
        output_format=args.output_format,
    )
    validate_package_not_filtered(config.package, config.filter_substring)
    return config


def create_provider(config: Config) -> DependencyProvider:
    """Choose where relations between packages come from."""
    if not config.test_mode:
        return make_registry_provider(config.repo)
    if config.reverse:
        return make_reverse_provider(config.repo, config.package)
    return make_file_provider(config.repo, config.package)


def render_graph(config: Config, graph: Graph) -> List[str]:
    """Render the graph in the output format chosen by the user."""
    if config.output_format == FORMAT_TEXT:
        if config.reverse:
            return format_reverse_graph(graph, config.max_depth)
        return format_graph(graph, config.max_depth)
    return format_plantuml(graph, config.max_depth, config.reverse)


def collect_graph(config: Config) -> Graph:
    """Build the dependency graph of the requested package."""
    return build_graph(
        config.package,
        create_provider(config),
        config.max_depth,
        config.filter_substring,
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Parse options, build the dependency graph and print it."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config(args)
    except ConfigError as error:
        parser.error(str(error))
    try:
        graph = collect_graph(config)
    except RepositoryError as error:
        print(f"depviz: error: {error}", file=sys.stderr)
        return EXIT_FAILURE
    print("\n".join(render_graph(config, graph)))
    return EXIT_OK
