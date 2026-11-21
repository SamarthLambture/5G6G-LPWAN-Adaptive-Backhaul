"""Start the self-contained LPWAN Edge Intelligence browser dashboard."""
from __future__ import annotations

import argparse
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"


class DashboardHandler(SimpleHTTPRequestHandler):
    """Static frontend handler with a lightweight health route and no stale caching."""

    server_version = "LPWAN-Dashboard/1.2.0"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler naming
        if urlsplit(self.path).path == "/healthz":
            payload = {
                "ok": (FRONTEND / "index.html").is_file()
                and (FRONTEND / "app.js").is_file()
                and (FRONTEND / "data" / "app-data.json").is_file(),
                "frontend": str(FRONTEND),
                "index": (FRONTEND / "index.html").is_file(),
                "app_js": (FRONTEND / "app.js").is_file(),
                "dataset": (FRONTEND / "data" / "app-data.json").is_file(),
            }
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(200 if payload["ok"] else 503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self) -> None:
        # Prevent the browser from holding an outdated JS bundle or app-data.json
        # after the user replaces the Simulation directory with a newer build.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[dashboard] {self.address_string()} - {fmt % args}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LPWAN Edge Intelligence dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (FRONTEND / "index.html").is_file():
        print(f"ERROR: frontend/index.html is missing under {FRONTEND}", file=sys.stderr)
        return 2
    if not (FRONTEND / "data" / "app-data.json").is_file():
        print(f"ERROR: frontend/data/app-data.json is missing under {FRONTEND}", file=sys.stderr)
        return 2

    handler = partial(DashboardHandler, directory=str(FRONTEND))
    try:
        server = ReusableThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        if getattr(exc, "errno", None) in (48, 98, 10048):
            print(
                f"ERROR: port {args.port} is already in use. Close the earlier dashboard terminal "
                f"or start this copy on another port with: py -3.13 run_app.py --port 8010",
                file=sys.stderr,
            )
            return 3
        print(f"ERROR: could not start dashboard server: {exc}", file=sys.stderr)
        return 2

    url_host = "127.0.0.1" if args.host in ("0.0.0.0", "") else args.host
    print("LPWAN Edge Intelligence dashboard is ready.")
    print(f"Open: http://{url_host}:{args.port}")
    print(f"Health: http://{url_host}:{args.port}/healthz")
    print(f"Serving: {FRONTEND}")
    print("Keep this terminal open. Press Ctrl+C to stop the server.")
    try:
        with server:
            server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nDashboard server stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
