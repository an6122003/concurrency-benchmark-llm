"""Platform-appropriate application data locations."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path


def app_data_dir() -> Path:
    """Per-user writable data dir: AppData / Application Support / XDG."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / "HardwareAIBenchmark"
    path.mkdir(parents=True, exist_ok=True)
    return path


def results_dir() -> Path:
    """Where benchmark result folders are written (user-visible Documents folder)."""
    docs = Path.home() / "Documents"
    base = docs if docs.exists() else Path.home()
    path = base / "HardwareAIBenchmark"
    path.mkdir(parents=True, exist_ok=True)
    return path


def outbox_dir() -> Path:
    """Upload-ready payloads waiting to be sent."""
    path = app_data_dir() / "outbox"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def anonymous_machine_id() -> str:
    """Stable random id, generated once and stored locally. Not derived from
    hardware or hostname, so it cannot be reversed into anything personal."""
    marker = app_data_dir() / "machine-id"
    if marker.exists():
        return marker.read_text(encoding="utf-8").strip()
    value = uuid.uuid4().hex[:16]
    marker.write_text(value, encoding="utf-8")
    return value


def repo_root() -> Path:
    """Root of the source checkout (dev mode) or the frozen bundle dir."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]
