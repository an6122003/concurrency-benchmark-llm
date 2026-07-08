"""Canonical result schema (result.json), schema v1.

Wraps the engine's results.json into a versioned, validated, checksummed
document that the website API accepts. Stdlib only — dataclasses plus explicit
validation keep the packaged app small (swap in pydantic later if the schema
grows teeth).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from .. import APP_VERSION, BENCHMARK_SUITE_VERSION, SCHEMA_VERSION
from .config import BenchmarkConfig
from .paths import anonymous_machine_id

REQUIRED_TOP_KEYS = (
    "result_id", "schema_version", "app_version", "benchmark_suite_version",
    "timestamp", "status", "platform", "system", "config", "results", "checksum",
)

# Same thresholds the community database uses for "comfortable users".
COMFORT_MIN_PER_USER_TPS = 8.0
COMFORT_MAX_TTFT_S = 3.0


def _derive_scores(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    peak_tps, best_users, comfortable = 0.0, None, 0
    single_tps = ttft_1u = None
    for s in summaries:
        agg = s.get("aggregate_output_tps") or 0
        users = s.get("concurrency") or 0
        per_user = s.get("avg_per_request_tps")
        ttft = s.get("avg_ttft_s")
        ok = s.get("requests") and s.get("success") == s.get("requests")
        if agg > peak_tps:
            peak_tps, best_users = agg, users
        if users == 1:
            single_tps, ttft_1u = per_user, ttft
        if ok and (per_user or 0) >= COMFORT_MIN_PER_USER_TPS and (ttft is None or ttft <= COMFORT_MAX_TTFT_S):
            comfortable = max(comfortable, users)
    return {
        "peak_aggregate_tps": round(peak_tps, 2) if peak_tps else None,
        "best_concurrency": best_users,
        "comfortable_users": comfortable or None,
        "single_user_tps": round(single_tps, 2) if single_tps else None,
        "ttft_1u_s": round(ttft_1u, 3) if ttft_1u is not None else None,
    }


def _checksum(document: Dict[str, Any]) -> str:
    payload = {k: v for k, v in document.items() if k != "checksum"}
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_result(
    config: BenchmarkConfig,
    system_info: Dict[str, Any],
    engine_results: Optional[Dict[str, Any]],
    status: str,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Assemble the canonical result document from a finished (or failed) run."""
    summaries = (engine_results or {}).get("summaries") or []
    engine_meta = (engine_results or {}).get("meta") or {}
    engine_config = engine_meta.get("benchmark_config") or {}

    document: Dict[str, Any] = {
        "result_id": uuid.uuid4().hex,
        "schema_version": SCHEMA_VERSION,
        "app_version": APP_VERSION,
        "benchmark_suite_version": BENCHMARK_SUITE_VERSION,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,                                     # completed | cancelled | failed
        "user_alias": config.user_alias or None,
        "anonymous_machine_id": anonymous_machine_id(),
        "platform": system_info.get("platform", {}),
        "system": {
            "cpu": system_info.get("cpu", {}),
            "memory": system_info.get("memory", {}),
            "gpu": system_info.get("gpu", {}),
            "backends": system_info.get("backends", []),
        },
        "config": config.to_dict(include_app_fields=False),
        "model": {
            "name": config.model,
            "quantization": config.quantization or engine_config.get("model_quantization"),
            "context_size": config.context_size or engine_config.get("context_size"),
        },
        "results": {
            "summaries": summaries,
            "derived": _derive_scores(summaries),
        },
        "errors": errors or [],
        "warnings": warnings or [],
    }
    document["checksum"] = _checksum(document)
    return document


def validate_result(document: Dict[str, Any]) -> List[str]:
    """Schema-level problems; empty list means valid."""
    problems: List[str] = []
    for key in REQUIRED_TOP_KEYS:
        if key not in document:
            problems.append(f"missing field: {key}")
    if document.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION}")
    if document.get("status") not in ("completed", "cancelled", "failed"):
        problems.append("status must be completed, cancelled, or failed")
    if document.get("status") == "completed" and not (document.get("results") or {}).get("summaries"):
        problems.append("completed result has no summaries")
    if "checksum" in document and document["checksum"] != _checksum(document):
        problems.append("checksum mismatch — document was modified")
    return problems
