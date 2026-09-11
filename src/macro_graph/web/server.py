"""Zero-framework local HTTP server for reports, snapshots, and causal graphs."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from macro_graph.settings import Settings

STATIC_DIR = Path(__file__).with_name("static")


class DashboardData:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def latest_snapshot_path(self) -> Path | None:
        candidates = sorted((self.output_dir / "snapshots").glob("market_snapshot_*.json"))
        return candidates[-1] if candidates else None

    def latest_report_path(self) -> Path | None:
        candidates = sorted((self.output_dir / "reports").glob("????-??-??.md"))
        return candidates[-1] if candidates else None

    def snapshot(self) -> dict:
        path = self.latest_snapshot_path()
        if path is None:
            return {"error": "NO_SNAPSHOT", "message": "请先运行 macro-graph-daily。"}
        return json.loads(path.read_text(encoding="utf-8"))

    def report(self) -> dict:
        path = self.latest_report_path()
        if path is None:
            return {"error": "NO_REPORT", "content": "暂无日报。"}
        return {"date": path.stem, "content": path.read_text(encoding="utf-8")}

    def graph(self) -> dict:
        path = self.output_dir / "graphs" / "graph.json"
        if not path.exists():
            return {"error": "NO_GRAPH", "message": "暂无图谱。"}
        return json.loads(path.read_text(encoding="utf-8"))


def make_handler(data: DashboardData):
    class DashboardHandler(BaseHTTPRequestHandler):
        server_version = "MacroGraph/0.1"

        def do_GET(self) -> None:
            route = urlparse(self.path).path
            if route == "/api/health":
                self._send_json({"status": "ok", "snapshot": bool(data.latest_snapshot_path())})
                return
            if route == "/api/snapshot":
                self._send_json(data.snapshot())
                return
            if route == "/api/report":
                self._send_json(data.report())
                return
            if route == "/api/graph":
                self._send_json(data.graph())
                return
            self._send_static(route)

        def _send_json(self, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, route: str) -> None:
            relative = "index.html" if route in {"", "/"} else route.lstrip("/")
            candidate = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if not candidate.is_file():
                candidate = STATIC_DIR / "index.html"
            body = candidate.read_bytes()
            mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            if mime.startswith("text/") or mime in {"application/javascript", "application/json"}:
                mime += "; charset=utf-8"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            print(f"[web] {self.address_string()} {format % args}")

    return DashboardHandler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local Macro Graph dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.load()
    server = ThreadingHTTPServer(
        (args.host, args.port), make_handler(DashboardData(settings.output_dir))
    )
    print(f"Macro Graph dashboard: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
