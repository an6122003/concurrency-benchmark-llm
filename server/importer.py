"""Import benchmark results into the SQLite database.

Accepts three input shapes:

1. A benchmark run folder or its ``results.json`` produced by
   ``ai_concurrent_benchmark.py`` (``{"meta": ..., "summaries": [...]}``).
   Suite output folders from ``benchmark_suite.py`` are scanned recursively.
2. A database-format JSON array (the shape of ``web/sample-data.json``).
3. A single database-format JSON object.

Usage:
    python server/importer.py path [path ...] [--db data/benchmarks.db]
        [--source "who ran it"] [--verified Verified|Community|Estimated]
        [--price 1199] [--replace]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db as dbmod

MODEL_FAMILIES = [
    "gemma", "qwen", "llama", "mistral", "mixtral", "deepseek", "phi",
    "gpt-oss", "granite", "command", "yi", "smollm", "falcon", "starcoder",
    "codestral", "aya", "olmo", "nemotron", "exaone", "glm", "internlm",
]


def _parse_size_b(model_name: str) -> Optional[float]:
    """Largest '<n>b' token wins: 'gemma-4-26b-a4b' is a 26B model whose
    'a4b' suffix is the active-parameter count, not the size."""
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*[bB]\b", model_name)
    if matches:
        return max(float(m) for m in matches)
    return None


def _guess_family(model_name: str) -> str:
    lowered = model_name.lower()
    for family in MODEL_FAMILIES:
        if family in lowered:
            return family.capitalize() if family != "gpt-oss" else "GPT-OSS"
    return re.split(r"[\s:/_-]", model_name, 1)[0].capitalize() or "Unknown"


def _guess_quant(model_name: str) -> Optional[str]:
    match = re.search(r"(q\d(?:_[a-z0-9_]+)?|fp16|bf16|fp8|int8|int4|mxfp4)", model_name.lower())
    return match.group(1).upper() if match else None


def _first_gpu(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Pick the most plausible benchmark GPU: the one with the most VRAM."""
    detected = (meta.get("gpu") or {}).get("detected") or []
    if not detected:
        return {}
    return max(detected, key=lambda gpu: gpu.get("vram_total_bytes") or 0)


def _parse_gb(text: Any) -> Optional[float]:
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    match = re.search(r"(\d+(?:\.\d+)?)\s*([GMT]i?B)?", str(text), re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = (match.group(2) or "GB").upper()
    if unit.startswith("M"):
        value /= 1024
    elif unit.startswith("T"):
        value *= 1024
    return round(value, 1)


def _guess_brand(vendor_or_name: str) -> str:
    lowered = vendor_or_name.lower()
    for key, brand in [
        ("nvidia", "NVIDIA"), ("geforce", "NVIDIA"), ("rtx", "NVIDIA"),
        ("amd", "AMD"), ("radeon", "AMD"), ("apple", "Apple"),
        ("intel", "Intel"), ("arc", "Intel"), ("qualcomm", "Qualcomm"),
    ]:
        if key in lowered:
            return brand
    return vendor_or_name or "Unknown"


def convert_results_json(raw: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convert an ai_concurrent_benchmark.py results.json into a database record."""
    overrides = overrides or {}
    meta = raw.get("meta") or {}
    config = meta.get("benchmark_config") or {}
    gpu = _first_gpu(meta)

    model_name = config.get("model") or "Unknown"
    gpu_name = config.get("gpu_label") or gpu.get("name") or "Unknown hardware"
    vram_gb = _parse_gb(gpu.get("vram_total_human"))
    backend = config.get("runtime_label") or (meta.get("runtime") or {}).get("backend")

    run_points = []
    for summary in raw.get("summaries") or []:
        requests = summary.get("requests") or 0
        success = summary.get("success") or 0
        run_points.append({
            "users": summary.get("concurrency"),
            "aggregateTps": summary.get("aggregate_output_tps"),
            "perUserTps": summary.get("avg_per_request_tps"),
            "minPerUserTps": summary.get("min_per_request_tps"),
            "maxPerUserTps": summary.get("max_per_request_tps"),
            "ttft": summary.get("avg_ttft_s"),
            "p95Ttft": summary.get("p95_ttft_s"),
            "avgLatency": summary.get("avg_latency_s"),
            "p95Latency": summary.get("p95_latency_s"),
            "successRate": round(success / requests * 100, 1) if requests else None,
            "vramUsedGb": None,
        })
    run_points.sort(key=lambda p: p.get("users") or 0)

    record = {
        "testedAt": overrides.get("testedAt") or meta.get("timestamp") or dt.date.today().isoformat(),
        "source": overrides.get("source") or "local import",
        "notes": config.get("notes"),
        "hardware": {
            "brand": _guess_brand(gpu.get("vendor") or gpu_name),
            "model": gpu_name,
            "class": overrides.get("hardwareClass") or "GPU",
            "vramGb": overrides.get("vramGb") or vram_gb,
            "priceUsd": overrides.get("priceUsd"),
        },
        "system": {
            "os": (meta.get("os") or {}).get("system") or "Unknown",
            "osVersion": (meta.get("os") or {}).get("release"),
            "cpu": (meta.get("cpu") or {}).get("processor") or (meta.get("cpu") or {}).get("name"),
            "ramGb": _parse_gb((meta.get("memory") or {}).get("total_human")),
        },
        "software": {
            "runtime": {"lmstudio": "LM Studio", "ollama": "Ollama", "ollama-native": "Ollama"}.get(
                config.get("server"), config.get("server") or "Unknown"),
            "backend": backend,
            "endpoint": config.get("base_url"),
        },
        "model": {
            "family": _guess_family(model_name),
            "name": model_name,
            "sizeB": _parse_size_b(model_name),
            "quantization": config.get("model_quantization") or _guess_quant(model_name),
            "format": "GGUF",
            "context": config.get("context_size"),
        },
        "benchmark": {
            "maxTokens": config.get("max_tokens_per_request"),
            "verified": overrides.get("verified") or "Community",
            "runPoints": run_points,
        },
        "raw": raw,
    }
    return record


def iter_results_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    yield from sorted(path.rglob("results.json"))


def import_path(conn: sqlite3.Connection, path: Path, overrides: Dict[str, Any], replace: bool = False) -> List[str]:
    imported: List[str] = []
    for file in iter_results_files(path):
        data = json.loads(file.read_text(encoding="utf-8"))
        records: List[Dict[str, Any]]
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "summaries" in data:
            records = [convert_results_json(data, overrides)]
        elif isinstance(data, dict) and "benchmark" in data:
            records = [data]
        else:
            print(f"skip {file}: unrecognized JSON shape", file=sys.stderr)
            continue
        for record in records:
            run_id = dbmod.insert_run(conn, record, replace=replace)
            imported.append(run_id)
            print(f"imported {run_id}  ({file.name})")
    return imported


def main() -> int:
    parser = argparse.ArgumentParser(description="Import benchmark results into the database")
    parser.add_argument("paths", nargs="+", help="results.json files, run folders, suite folders, or database-format JSON")
    parser.add_argument("--db", default=str(dbmod.DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--source", help="Submitter/source label")
    parser.add_argument("--verified", choices=["Verified", "Community", "Estimated", "Archived"], help="Data quality level")
    parser.add_argument("--price", type=float, dest="price_usd", help="Hardware price in USD at test time")
    parser.add_argument("--vram", type=float, dest="vram_gb", help="Override VRAM/unified memory in GB")
    parser.add_argument("--hardware-class", dest="hardware_class", help="GPU, Integrated GPU, CPU, NPU, Multi-GPU")
    parser.add_argument("--replace", action="store_true", help="Replace runs that already exist")
    args = parser.parse_args()

    overrides = {
        "source": args.source,
        "verified": args.verified,
        "priceUsd": args.price_usd,
        "vramGb": args.vram_gb,
        "hardwareClass": args.hardware_class,
    }
    overrides = {key: value for key, value in overrides.items() if value is not None}

    conn = dbmod.connect(args.db)
    total = 0
    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"not found: {path}", file=sys.stderr)
            return 1
        total += len(import_path(conn, path, overrides, replace=args.replace))
    print(f"done: {total} run(s) into {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
