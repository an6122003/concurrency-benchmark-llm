"""Write the app-level artifacts next to the engine's own outputs.

The engine already produces report.html, report.md, results.csv, results.json
and metadata.json in the run folder. This module adds:

  result.json     canonical schema document (see result_schema)
  app_metadata.json  app/schema/suite versions plus a file inventory
  raw_logs.txt    written by the runner (referenced here for completeness)
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .. import APP_NAME, APP_VERSION, BENCHMARK_SUITE_VERSION, SCHEMA_VERSION


def load_engine_results(out_dir: Path) -> Optional[Dict[str, Any]]:
    path = out_dir / "results.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_result_files(out_dir: Path, result_document: Dict[str, Any]) -> Dict[str, Path]:
    """Write result.json + app_metadata.json; return the full artifact map."""
    out_dir.mkdir(parents=True, exist_ok=True)

    result_path = out_dir / "result.json"
    result_path.write_text(json.dumps(result_document, indent=2), encoding="utf-8")

    metadata = {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "benchmark_suite_version": BENCHMARK_SUITE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "result_id": result_document.get("result_id"),
        "files": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
    }
    metadata_path = out_dir / "app_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    artifacts = {"result.json": result_path, "app_metadata.json": metadata_path}
    for name in ("report.html", "report.md", "results.json", "results.csv",
                 "metadata.json", "raw_logs.txt"):
        path = out_dir / name
        if path.exists():
            artifacts[name] = path
    return artifacts
