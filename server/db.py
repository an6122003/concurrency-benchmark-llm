"""SQLite storage for the AI hardware benchmark database.

Zero-dependency: uses only the Python standard library. The schema follows
BENCHMARK_DATABASE_PLAN.md: dimension tables for hardware, system, software
stack, and model, plus a runs fact table and per-concurrency run_points.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS hardware (
    id INTEGER PRIMARY KEY,
    brand TEXT NOT NULL DEFAULT 'Unknown',
    model TEXT NOT NULL DEFAULT 'Unknown',
    class TEXT NOT NULL DEFAULT 'GPU',
    architecture TEXT,
    vram_gb REAL,
    memory_type TEXT,
    bus_width_bit INTEGER,
    bandwidth_gbps REAL,
    tdp_w REAL,
    board_partner TEXT,
    price_usd REAL,
    UNIQUE(brand, model, class, vram_gb, board_partner)
);

CREATE TABLE IF NOT EXISTS systems (
    id INTEGER PRIMARY KEY,
    os TEXT NOT NULL DEFAULT 'Unknown',
    os_version TEXT,
    cpu TEXT,
    ram_gb REAL,
    UNIQUE(os, os_version, cpu, ram_gb)
);

CREATE TABLE IF NOT EXISTS software (
    id INTEGER PRIMARY KEY,
    runtime TEXT NOT NULL DEFAULT 'Unknown',
    runtime_version TEXT,
    backend TEXT,
    driver TEXT,
    endpoint TEXT,
    UNIQUE(runtime, runtime_version, backend, driver, endpoint)
);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY,
    family TEXT NOT NULL DEFAULT 'Unknown',
    name TEXT NOT NULL DEFAULT 'Unknown',
    size_b REAL,
    quantization TEXT,
    format TEXT,
    UNIQUE(family, name, size_b, quantization, format)
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    hardware_id INTEGER NOT NULL REFERENCES hardware(id),
    system_id INTEGER NOT NULL REFERENCES systems(id),
    software_id INTEGER NOT NULL REFERENCES software(id),
    model_id INTEGER NOT NULL REFERENCES models(id),
    context_size INTEGER,
    max_tokens INTEGER,
    prompt_tokens_avg REAL,
    tested_at TEXT,
    source TEXT,
    verified TEXT NOT NULL DEFAULT 'Community',
    notes TEXT,
    comfortable_users INTEGER,
    max_success_users INTEGER,
    peak_aggregate_tps REAL,
    best_concurrency INTEGER,
    single_user_tps REAL,
    ttft_1u REAL,
    p95_latency_1u REAL,
    price_per_comfortable_user REAL,
    tps_per_dollar REAL,
    fairness_score REAL,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS run_points (
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    users INTEGER NOT NULL,
    aggregate_tps REAL,
    per_user_tps REAL,
    min_per_user_tps REAL,
    max_per_user_tps REAL,
    ttft_s REAL,
    p95_ttft_s REAL,
    avg_latency_s REAL,
    p95_latency_s REAL,
    success_rate REAL,
    vram_used_gb REAL,
    PRIMARY KEY (run_id, users)
);

CREATE INDEX IF NOT EXISTS idx_runs_hardware ON runs(hardware_id);
CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model_id);
CREATE INDEX IF NOT EXISTS idx_runs_software ON runs(software_id);
"""

# Thresholds for the "comfortable users" derived score: every request must
# succeed, each user still gets a usable speed, and first token is not painful.
COMFORT_MIN_PER_USER_TPS = 8.0
COMFORT_MAX_TTFT_S = 3.0

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "benchmarks.db"


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def _norm(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _upsert_dimension(conn: sqlite3.Connection, table: str, fields: Dict[str, Any]) -> int:
    fields = {key: _norm(value) for key, value in fields.items()}
    where = " AND ".join(f"{key} IS ?" for key in fields)
    row = conn.execute(f"SELECT id FROM {table} WHERE {where}", list(fields.values())).fetchone()
    if row:
        return row["id"]
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    cur = conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(fields.values()))
    return cur.lastrowid


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "run"


def make_run_id(record: Dict[str, Any]) -> str:
    hardware = record.get("hardware", {})
    model = record.get("model", {})
    software = record.get("software", {})
    base = "-".join(
        _slugify(str(part))
        for part in [
            hardware.get("model", "hw"),
            model.get("name", "model"),
            model.get("quantization", ""),
            software.get("runtime", ""),
        ]
        if part
    )
    digest = hashlib.sha1(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()[:8]
    return f"{base}-{digest}"


def compute_derived(record: Dict[str, Any]) -> Dict[str, Any]:
    """Compute the derived scores defined in BENCHMARK_DATABASE_PLAN.md."""
    bench = record.get("benchmark", {})
    points = bench.get("runPoints") or []
    price = record.get("hardware", {}).get("priceUsd")

    peak_tps, best_users = 0.0, None
    comfortable, max_success = 0, 0
    single_tps = ttft_1u = p95_1u = None
    fairness: List[float] = []

    for point in points:
        users = point.get("users") or 0
        agg = point.get("aggregateTps") or 0
        per_user = point.get("perUserTps")
        ttft = point.get("ttft")
        success = point.get("successRate")
        if agg > peak_tps:
            peak_tps, best_users = agg, users
        if users == 1:
            single_tps = per_user or agg or None
            ttft_1u = ttft
            p95_1u = point.get("p95Latency")
        if success is not None and success >= 100:
            max_success = max(max_success, users)
            if (per_user or 0) >= COMFORT_MIN_PER_USER_TPS and (ttft is None or ttft <= COMFORT_MAX_TTFT_S):
                comfortable = max(comfortable, users)
        min_tps, avg_tps = point.get("minPerUserTps"), per_user
        if min_tps and avg_tps:
            fairness.append(min_tps / avg_tps)

    return {
        "comfortable_users": comfortable or None,
        "max_success_users": max_success or None,
        "peak_aggregate_tps": round(peak_tps, 2) if peak_tps else None,
        "best_concurrency": best_users,
        "single_user_tps": round(single_tps, 2) if single_tps else None,
        "ttft_1u": round(ttft_1u, 3) if ttft_1u is not None else None,
        "p95_latency_1u": round(p95_1u, 2) if p95_1u is not None else None,
        "price_per_comfortable_user": round(price / comfortable, 2) if price and comfortable else None,
        "tps_per_dollar": round(peak_tps / price, 4) if price and peak_tps else None,
        "fairness_score": round(sum(fairness) / len(fairness), 3) if fairness else None,
    }


def insert_run(conn: sqlite3.Connection, record: Dict[str, Any], replace: bool = False) -> str:
    """Insert one database-format record (the shape used by web/sample-data.json)."""
    hardware = record.get("hardware", {})
    system = record.get("system", {})
    software = record.get("software", {})
    model = record.get("model", {})
    bench = record.get("benchmark", {})

    hardware_id = _upsert_dimension(conn, "hardware", {
        "brand": hardware.get("brand") or "Unknown",
        "model": hardware.get("model") or "Unknown",
        "class": hardware.get("class") or "GPU",
        "architecture": hardware.get("architecture"),
        "vram_gb": hardware.get("vramGb"),
        "memory_type": hardware.get("memoryType"),
        "bus_width_bit": hardware.get("busWidth"),
        "bandwidth_gbps": hardware.get("bandwidthGbps"),
        "tdp_w": hardware.get("tdpW"),
        "board_partner": hardware.get("boardPartner"),
        "price_usd": hardware.get("priceUsd"),
    })
    system_id = _upsert_dimension(conn, "systems", {
        "os": system.get("os") or "Unknown",
        "os_version": system.get("osVersion"),
        "cpu": system.get("cpu"),
        "ram_gb": system.get("ramGb"),
    })
    software_id = _upsert_dimension(conn, "software", {
        "runtime": software.get("runtime") or "Unknown",
        "runtime_version": software.get("runtimeVersion"),
        "backend": software.get("backend"),
        "driver": software.get("driver"),
        "endpoint": software.get("endpoint"),
    })
    model_id = _upsert_dimension(conn, "models", {
        "family": model.get("family") or "Unknown",
        "name": model.get("name") or "Unknown",
        "size_b": model.get("sizeB"),
        "quantization": model.get("quantization"),
        "format": model.get("format"),
    })

    run_id = record.get("id") or make_run_id(record)
    derived = compute_derived(record)
    verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
    cur = conn.execute(
        f"""{verb} INTO runs (
            id, hardware_id, system_id, software_id, model_id,
            context_size, max_tokens, prompt_tokens_avg, tested_at, source,
            verified, notes, comfortable_users, max_success_users,
            peak_aggregate_tps, best_concurrency, single_user_tps, ttft_1u,
            p95_latency_1u, price_per_comfortable_user, tps_per_dollar,
            fairness_score, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id, hardware_id, system_id, software_id, model_id,
            model.get("context"), bench.get("maxTokens"), bench.get("promptTokensAvg"),
            record.get("testedAt"), record.get("source"),
            bench.get("verified") or record.get("verified") or "Community",
            record.get("notes"),
            derived["comfortable_users"], derived["max_success_users"],
            derived["peak_aggregate_tps"], derived["best_concurrency"],
            derived["single_user_tps"], derived["ttft_1u"], derived["p95_latency_1u"],
            derived["price_per_comfortable_user"], derived["tps_per_dollar"],
            derived["fairness_score"],
            json.dumps(record.get("raw")) if record.get("raw") else None,
        ),
    )
    if cur.rowcount == 0:
        return run_id  # already present, INSERT OR IGNORE skipped it

    conn.execute("DELETE FROM run_points WHERE run_id = ?", (run_id,))
    for point in bench.get("runPoints") or []:
        conn.execute(
            """INSERT OR REPLACE INTO run_points (
                run_id, users, aggregate_tps, per_user_tps, min_per_user_tps,
                max_per_user_tps, ttft_s, p95_ttft_s, avg_latency_s,
                p95_latency_s, success_rate, vram_used_gb
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, point.get("users"), point.get("aggregateTps"),
                point.get("perUserTps"), point.get("minPerUserTps"),
                point.get("maxPerUserTps"), point.get("ttft"), point.get("p95Ttft"),
                point.get("avgLatency"), point.get("p95Latency"),
                point.get("successRate"), point.get("vramUsedGb"),
            ),
        )
    conn.commit()
    return run_id


RUN_SELECT = """
SELECT r.*,
       h.brand, h.model AS hw_model, h.class AS hw_class, h.architecture,
       h.vram_gb, h.memory_type, h.bus_width_bit, h.bandwidth_gbps, h.tdp_w,
       h.board_partner, h.price_usd,
       s.os, s.os_version, s.cpu, s.ram_gb,
       sw.runtime, sw.runtime_version, sw.backend, sw.driver, sw.endpoint,
       m.family, m.name AS model_name, m.size_b, m.quantization, m.format
FROM runs r
JOIN hardware h ON h.id = r.hardware_id
JOIN systems s ON s.id = r.system_id
JOIN software sw ON sw.id = r.software_id
JOIN models m ON m.id = r.model_id
"""


def row_to_record(row: sqlite3.Row, points: Optional[List[sqlite3.Row]] = None) -> Dict[str, Any]:
    """Convert a joined row back to the nested JSON shape the frontend uses."""
    record = {
        "id": row["id"],
        "testedAt": row["tested_at"],
        "source": row["source"],
        "notes": row["notes"],
        "hardware": {
            "brand": row["brand"], "model": row["hw_model"], "class": row["hw_class"],
            "architecture": row["architecture"], "vramGb": row["vram_gb"],
            "memoryType": row["memory_type"], "busWidth": row["bus_width_bit"],
            "bandwidthGbps": row["bandwidth_gbps"], "tdpW": row["tdp_w"],
            "boardPartner": row["board_partner"], "priceUsd": row["price_usd"],
        },
        "system": {
            "os": row["os"], "osVersion": row["os_version"],
            "cpu": row["cpu"], "ramGb": row["ram_gb"],
        },
        "software": {
            "runtime": row["runtime"], "runtimeVersion": row["runtime_version"],
            "backend": row["backend"], "driver": row["driver"], "endpoint": row["endpoint"],
        },
        "model": {
            "family": row["family"], "name": row["model_name"], "sizeB": row["size_b"],
            "quantization": row["quantization"], "format": row["format"],
            "context": row["context_size"],
        },
        "benchmark": {
            "maxTokens": row["max_tokens"],
            "promptTokensAvg": row["prompt_tokens_avg"],
            "comfortableUsers": row["comfortable_users"],
            "maxSuccessUsers": row["max_success_users"],
            "peakAggregateTps": row["peak_aggregate_tps"],
            "bestConcurrency": row["best_concurrency"],
            "singleUserTps": row["single_user_tps"],
            "ttft1u": row["ttft_1u"],
            "p95Latency1u": row["p95_latency_1u"],
            "pricePerComfortableUser": row["price_per_comfortable_user"],
            "tpsPerDollar": row["tps_per_dollar"],
            "fairnessScore": row["fairness_score"],
            "verified": row["verified"],
        },
    }
    if points is not None:
        record["benchmark"]["runPoints"] = [
            {
                "users": p["users"], "aggregateTps": p["aggregate_tps"],
                "perUserTps": p["per_user_tps"], "minPerUserTps": p["min_per_user_tps"],
                "maxPerUserTps": p["max_per_user_tps"], "ttft": p["ttft_s"],
                "p95Ttft": p["p95_ttft_s"], "avgLatency": p["avg_latency_s"],
                "p95Latency": p["p95_latency_s"], "successRate": p["success_rate"],
                "vramUsedGb": p["vram_used_gb"],
            }
            for p in points
        ]
    return record


def fetch_points(conn: sqlite3.Connection, run_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM run_points WHERE run_id = ? ORDER BY users", (run_id,)
    ).fetchall()
