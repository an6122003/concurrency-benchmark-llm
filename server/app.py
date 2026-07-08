"""AI hardware benchmark database server.

Zero-dependency backend: Python standard library HTTP server + SQLite.
Serves the browsing frontend from ``web/`` and a JSON API:

    GET  /api/runs      filtered + sorted list (see FILTERS below)
    GET  /api/runs/{id} one run with per-concurrency points and raw JSON
    GET  /api/facets    distinct filter values with counts, and value ranges
    GET  /api/stats     headline numbers for the visible selection
    POST /api/import    JSON body: results.json, database record, or array

Run:
    python server/app.py [--port 8080] [--db data/benchmarks.db] [--seed]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db as dbmod
import importer

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
SEED_FILE = WEB_DIR / "sample-data.json"

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}

# Equality filters: query param -> SQL column
EQ_FILTERS = {
    "brand": "h.brand",
    "hardware_model": "h.model",
    "hardware_class": "h.class",
    "family": "m.family",
    "quant": "m.quantization",
    "runtime": "sw.runtime",
    "backend": "sw.backend",
    "os": "s.os",
    "verified": "r.verified",
}

# Range filters: query param -> (SQL expression, operator)
RANGE_FILTERS = {
    "min_vram": ("h.vram_gb", ">="),
    "max_vram": ("h.vram_gb", "<="),
    "min_price": ("h.price_usd", ">="),
    "max_price": ("h.price_usd", "<="),
    "min_users": ("r.comfortable_users", ">="),
    "min_size_b": ("m.size_b", ">="),
    "max_size_b": ("m.size_b", "<="),
    "min_context": ("r.context_size", ">="),
    "min_tps": ("r.peak_aggregate_tps", ">="),
    "max_ttft": ("r.ttft_1u", "<="),
}

SORT_KEYS = {
    "comfortable_users": "r.comfortable_users",
    "peak_aggregate_tps": "r.peak_aggregate_tps",
    "single_user_tps": "r.single_user_tps",
    "ttft": "r.ttft_1u",
    "p95": "r.p95_latency_1u",
    "value": "r.price_per_comfortable_user",
    "tps_per_dollar": "r.tps_per_dollar",
    "vram": "h.vram_gb",
    "price": "h.price_usd",
    "size_b": "m.size_b",
    "tested_at": "r.tested_at",
}
# Sorts where smaller is better default to ascending.
ASC_DEFAULT = {"ttft", "p95", "value", "price"}

PRESETS = {
    "team": {"min_users": "5"},
    "thirtyB": {"min_size_b": "27"},
    "budget": {"max_price": "1000"},
    "nonCuda": {"exclude_backend": "cuda"},
    "lowLatency": {"max_ttft": "0.75"},
    "highContext": {"min_context": "16384"},
    "valueKing": {"sort": "tps_per_dollar"},
}

FACET_FIELDS = {
    "brand": "h.brand",
    "hardwareModel": "h.model",
    "hardwareClass": "h.class",
    "family": "m.family",
    "quantization": "m.quantization",
    "runtime": "sw.runtime",
    "backend": "sw.backend",
    "os": "s.os",
    "verified": "r.verified",
}

SEARCH_COLUMNS = [
    "h.brand", "h.model", "h.board_partner", "m.family", "m.name",
    "m.quantization", "sw.runtime", "sw.backend", "sw.driver", "s.os", "s.cpu",
]


def build_query(params: Dict[str, str]) -> Tuple[str, List[Any], str]:
    """Return (WHERE clause, bind values, ORDER BY clause) for /api/runs."""
    preset = params.get("preset")
    if preset in PRESETS:
        merged = dict(PRESETS[preset])
        merged.update({k: v for k, v in params.items() if v})
        params = merged

    where, values = [], []
    for param, column in EQ_FILTERS.items():
        value = params.get(param)
        if value:
            where.append(f"{column} = ?")
            values.append(value)
    for param, (column, op) in RANGE_FILTERS.items():
        value = params.get(param)
        if value:
            try:
                values.append(float(value))
            except ValueError:
                continue
            where.append(f"{column} {op} ?")
    exclude_backend = params.get("exclude_backend")
    if exclude_backend:
        where.append("LOWER(COALESCE(sw.backend, '')) NOT LIKE ?")
        values.append(f"%{exclude_backend.lower()}%")
    search = params.get("search", "").strip().lower()
    if search:
        haystack = " || ' ' || ".join(f"COALESCE({col}, '')" for col in SEARCH_COLUMNS)
        where.append(f"LOWER({haystack}) LIKE ?")
        values.append(f"%{search}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sort = params.get("sort", "comfortable_users")
    column = SORT_KEYS.get(sort, SORT_KEYS["comfortable_users"])
    order = params.get("order") or ("asc" if sort in ASC_DEFAULT else "desc")
    direction = "ASC" if order == "asc" else "DESC"
    # NULLs always last so incomplete runs do not float to the top.
    order_sql = f"ORDER BY {column} IS NULL, {column} {direction}, r.id"
    return where_sql, values, order_sql


class Api:
    def __init__(self, db_path: str):
        self.conn = dbmod.connect(db_path)
        self.lock = threading.Lock()

    def runs(self, params: Dict[str, str]) -> Dict[str, Any]:
        where_sql, values, order_sql = build_query(params)
        limit = min(int(params.get("limit", 200) or 200), 500)
        offset = max(int(params.get("offset", 0) or 0), 0)
        with self.lock:
            total = self.conn.execute(
                f"SELECT COUNT(*) AS n FROM ({dbmod.RUN_SELECT} {where_sql})", values
            ).fetchone()["n"]
            rows = self.conn.execute(
                f"{dbmod.RUN_SELECT} {where_sql} {order_sql} LIMIT ? OFFSET ?",
                values + [limit, offset],
            ).fetchall()
            records = []
            for row in rows:
                points = dbmod.fetch_points(self.conn, row["id"])
                records.append(dbmod.row_to_record(row, points))
        return {"total": total, "limit": limit, "offset": offset, "runs": records}

    def run_detail(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            row = self.conn.execute(f"{dbmod.RUN_SELECT} WHERE r.id = ?", (run_id,)).fetchone()
            if not row:
                return None
            record = dbmod.row_to_record(row, dbmod.fetch_points(self.conn, run_id))
            if row["raw_json"]:
                record["raw"] = json.loads(row["raw_json"])
        return record

    def facets(self) -> Dict[str, Any]:
        joined = """FROM runs r
                    JOIN hardware h ON h.id = r.hardware_id
                    JOIN systems s ON s.id = r.system_id
                    JOIN software sw ON sw.id = r.software_id
                    JOIN models m ON m.id = r.model_id"""
        facets: Dict[str, Any] = {}
        with self.lock:
            for name, column in FACET_FIELDS.items():
                rows = self.conn.execute(
                    f"""SELECT {column} AS value, COUNT(*) AS count {joined}
                        WHERE {column} IS NOT NULL
                        GROUP BY {column} ORDER BY {column}"""
                ).fetchall()
                facets[name] = [{"value": r["value"], "count": r["count"]} for r in rows]
            ranges = self.conn.execute(
                """SELECT MIN(h.vram_gb) AS vram_min, MAX(h.vram_gb) AS vram_max,
                          MIN(h.price_usd) AS price_min, MAX(h.price_usd) AS price_max,
                          MAX(r.comfortable_users) AS users_max,
                          MAX(m.size_b) AS size_b_max
                   FROM runs r
                   JOIN hardware h ON h.id = r.hardware_id
                   JOIN models m ON m.id = r.model_id"""
            ).fetchone()
        facets["ranges"] = {key: ranges[key] for key in ranges.keys()}
        facets["presets"] = list(PRESETS.keys())
        facets["sortKeys"] = list(SORT_KEYS.keys())
        return facets

    def stats(self, params: Dict[str, str]) -> Dict[str, Any]:
        where_sql, values, _ = build_query(params)
        with self.lock:
            row = self.conn.execute(
                f"""SELECT COUNT(*) AS runs,
                           MAX(comfortable_users) AS best_users,
                           MAX(peak_aggregate_tps) AS top_tps,
                           MIN(price_per_comfortable_user) AS best_value,
                           MAX(tps_per_dollar) AS best_tps_per_dollar
                    FROM ({dbmod.RUN_SELECT} {where_sql})""", values
            ).fetchone()
        return {key: row[key] for key in row.keys()}

    def accept_benchmark_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Desktop-app uploads (POST /api/benchmark-results).

        Stores the full schema document under data/uploads/ and, when it holds
        usable summaries, imports a browsable run into the database."""
        if not isinstance(payload, dict) or "result_id" not in payload:
            raise ValueError("Expected a result document with a result_id")
        if payload.get("status") != "completed":
            raise ValueError("Only completed results can be published")
        summaries = (payload.get("results") or {}).get("summaries") or []
        if not summaries:
            raise ValueError("Result contains no benchmark summaries")

        uploads = ROOT / "data" / "uploads"
        uploads.mkdir(parents=True, exist_ok=True)
        result_id = re.sub(r"[^a-zA-Z0-9_-]", "", str(payload["result_id"]))[:64] or "unknown"
        (uploads / f"{result_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

        system = payload.get("system") or {}
        record = importer.convert_results_json(
            {"meta": {
                "os": {"system": (payload.get("platform") or {}).get("os", "Unknown"),
                        "release": (payload.get("platform") or {}).get("os_release")},
                "cpu": system.get("cpu") or {},
                "memory": system.get("memory") or {},
                "gpu": system.get("gpu") or {},
                "benchmark_config": {
                    "server": (payload.get("config") or {}).get("server"),
                    "model": (payload.get("model") or {}).get("name"),
                    "runtime_label": (payload.get("config") or {}).get("runtime_label"),
                    "gpu_label": (payload.get("config") or {}).get("gpu_label"),
                    "model_quantization": (payload.get("model") or {}).get("quantization"),
                    "context_size": (payload.get("model") or {}).get("context_size"),
                    "max_tokens_per_request": (payload.get("config") or {}).get("max_tokens"),
                },
             },
             "summaries": summaries},
            overrides={
                "source": payload.get("user_alias") or f"app upload {result_id[:8]}",
                "verified": "Community",
                "testedAt": (payload.get("timestamp") or "")[:10] or None,
            },
        )
        with self.lock:
            run_id = dbmod.insert_run(self.conn, record)
        return {"message": "result accepted", "run_id": run_id, "result_id": result_id}

    def import_payload(self, payload: Any, replace: bool = False) -> Dict[str, Any]:
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict) and "summaries" in payload:
            records = [importer.convert_results_json(payload)]
        elif isinstance(payload, dict) and "benchmark" in payload:
            records = [payload]
        else:
            raise ValueError("Expected results.json, a database record, or an array of records")
        with self.lock:
            ids = [dbmod.insert_run(self.conn, record, replace=replace) for record in records]
        return {"imported": ids}

    def seed(self) -> int:
        if not SEED_FILE.exists():
            return 0
        records = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        with self.lock:
            count = self.conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"]
            if count:
                return 0
            for record in records:
                record.setdefault("source", "sample data")
                dbmod.insert_run(self.conn, record)
        return len(records)


class Handler(BaseHTTPRequestHandler):
    api: Api  # set by serve()

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"{self.address_string()} {fmt % args}\n")

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if path.is_dir():
            path = path / "index.html"
        try:
            resolved = path.resolve()
            resolved.relative_to(ROOT)  # no escaping the repo
            body = resolved.read_bytes()
        except (OSError, ValueError):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME_TYPES.get(resolved.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = {key: values[0] for key, values in urllib.parse.parse_qs(parsed.query).items()}
        route = parsed.path
        try:
            if route == "/api/runs":
                self._send_json(self.api.runs(params))
            elif route.startswith("/api/runs/"):
                record = self.api.run_detail(urllib.parse.unquote(route[len("/api/runs/"):]))
                if record is None:
                    self._send_json({"error": "run not found"}, 404)
                else:
                    self._send_json(record)
            elif route == "/api/facets":
                self._send_json(self.api.facets())
            elif route == "/api/stats":
                self._send_json(self.api.stats(params))
            elif route == "/" or route == "":
                self.send_response(302)
                self.send_header("Location", "/web/")
                self.end_headers()
            elif route.startswith("/api/"):
                self._send_json({"error": "unknown endpoint"}, 404)
            else:
                self._send_file(ROOT / urllib.parse.unquote(route).lstrip("/"))
        except Exception as exc:  # keep the server alive on bad requests
            self._send_json({"error": str(exc)}, 500)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/api/import", "/api/benchmark-results"):
            self._send_json({"error": "unknown endpoint"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 50 * 1024 * 1024:
                self._send_json({"error": "payload too large"}, 413)
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if parsed.path == "/api/benchmark-results":
                result = self.api.accept_benchmark_result(payload)
            else:
                params = {key: values[0] for key, values in urllib.parse.parse_qs(parsed.query).items()}
                result = self.api.import_payload(payload, replace=params.get("replace") == "1")
            self._send_json(result, 201)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def serve(port: int, db_path: str, seed: bool) -> None:
    api = Api(db_path)
    if seed:
        seeded = api.seed()
        if seeded:
            print(f"seeded {seeded} sample run(s)")
    Handler.api = api
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"benchmark database on http://localhost:{port}/web/  (db: {db_path})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI hardware benchmark database server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8080)))
    parser.add_argument("--db", default=str(dbmod.DEFAULT_DB_PATH))
    parser.add_argument("--seed", action="store_true", help="Seed sample data when the database is empty")
    args = parser.parse_args()
    serve(args.port, args.db, args.seed)


if __name__ == "__main__":
    main()
