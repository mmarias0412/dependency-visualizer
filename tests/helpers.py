"""Shared helpers for tests: CLI runner and a mock npm registry."""

import io
import threading
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer

from cli import main

LOCALHOST = "127.0.0.1"
HTTP_NOT_FOUND = 404


def run_cli(*argv):
    """Run the CLI and return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(list(argv))
        except SystemExit as exit_info:
            code = exit_info.code
    return code, out.getvalue(), err.getvalue()


class _Handler(BaseHTTPRequestHandler):
    """Serve canned responses taken from the server's routes."""

    def do_GET(self):
        """Answer a GET request using the routes table."""
        status, body = self.server.routes.get(
            self.path, (HTTP_NOT_FOUND, b"{}")
        )
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        """Silence request logging."""


class MockRegistry:
    """Local HTTP server that imitates an npm registry."""

    def __init__(self, routes):
        self._server = HTTPServer((LOCALHOST, 0), _Handler)
        self._server.routes = routes
        self._thread = threading.Thread(target=self._server.serve_forever)

    def __enter__(self):
        self._thread.start()
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def __exit__(self, *exc_info):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()
