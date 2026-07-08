"""Locate and invoke the existing benchmark engine (ai_concurrent_benchmark.py).

The engine stays untouched at the repo root. In development the runner spawns
``python ai_concurrent_benchmark.py ...``; in a frozen build the app re-invokes
itself with ``--engine`` and this module dispatches into the bundled engine.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import List, Optional

from .paths import repo_root

ENGINE_FILENAME = "ai_concurrent_benchmark.py"

_engine_module: Optional[ModuleType] = None


def engine_path() -> Path:
    path = repo_root() / ENGINE_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"benchmark engine not found at {path}")
    return path


def load_engine() -> ModuleType:
    """Import the engine as a module (no side effects: it is __main__-guarded)."""
    global _engine_module
    if _engine_module is None:
        spec = importlib.util.spec_from_file_location("ai_concurrent_benchmark", engine_path())
        module = importlib.util.module_from_spec(spec)
        sys.modules["ai_concurrent_benchmark"] = module
        spec.loader.exec_module(module)
        _engine_module = module
    return _engine_module


def engine_command(cli_args: List[str]) -> List[str]:
    """Command line that runs the engine in a child process."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--engine", *cli_args]
    return [sys.executable, str(engine_path()), *cli_args]


def run_engine_worker(argv: List[str]) -> int:
    """Entry used by the frozen app when launched with --engine."""
    module = load_engine()
    return module.main(argv)
