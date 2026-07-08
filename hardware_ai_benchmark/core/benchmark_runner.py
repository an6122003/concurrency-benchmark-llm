"""Run the benchmark engine in a child process with live progress callbacks.

UI-agnostic: callers supply plain callables. The Qt layer wraps this in a
QThread and forwards callbacks as signals.
"""

from __future__ import annotations

import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from . import engine
from .config import BenchmarkConfig
from .runtime_manager import ManagedServer

USERS_LINE = re.compile(r"^users=\s*(\d+)\s+success=(\d+)/(\d+)")
WARMUP_LINE = re.compile(r"^\s*warmup (\d+)/(\d+)")


@dataclass
class RunOutcome:
    status: str = "failed"            # completed | cancelled | failed
    exit_code: Optional[int] = None
    out_dir: Optional[Path] = None
    log_lines: List[str] = field(default_factory=list)
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def duration_s(self) -> float:
        return max(0.0, self.finished_at - self.started_at)


class BenchmarkRunner:
    """One benchmark run = one child process. Safe to cancel from another thread."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.out_dir = config.resolved_out_dir()
        self._process: Optional[subprocess.Popen] = None
        self._managed: Optional[ManagedServer] = None
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()
        if self._managed:
            self._managed.stop()
        process = self._process
        if process and process.poll() is None:
            process.terminate()
            # escalate if it ignores SIGTERM
            def _kill():
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
            threading.Thread(target=_kill, daemon=True).start()

    def run(self,
            on_line: Callable[[str], None] = lambda line: None,
            on_stage: Callable[[str, float], None] = lambda stage, progress: None) -> RunOutcome:
        """Blocking. on_line(text) per output line; on_stage(name, 0..1)."""
        outcome = RunOutcome(started_at=time.time())
        groups = self.config.concurrency_list()
        total_groups = max(1, len(groups))
        done_groups = 0

        self.out_dir.mkdir(parents=True, exist_ok=True)
        outcome.out_dir = self.out_dir

        def log(line: str) -> None:
            outcome.log_lines.append(line)
            on_line(line)

        base_url = None
        if self.config.use_builtin_runtime:
            on_stage("Starting built-in AI runtime…", 0.01)
            self._managed = ManagedServer(
                Path(self.config.model_file),
                context_per_slot=self.config.context_size or 4096,
                parallel=min(8, max(groups, default=1)),
            )
            try:
                self._managed.start(on_line=log)
            except OSError as exc:
                outcome.error = str(exc)
                outcome.status = "cancelled" if self._cancelled.is_set() else "failed"
                outcome.finished_at = time.time()
                self._write_raw_logs(outcome)
                return outcome
            base_url = self._managed.base_url
            on_stage("Runtime ready — model loaded", 0.02)

        command = engine.engine_command(self.config.to_cli_args(self.out_dir, base_url=base_url))
        on_stage("Starting benchmark process…", 0.02 if base_url else 0.0)
        on_line("$ " + " ".join(command))

        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            outcome.error = f"Could not start benchmark process: {exc}"
            outcome.finished_at = time.time()
            if self._managed:
                self._managed.stop()
            self._write_raw_logs(outcome)
            return outcome

        for raw in self._process.stdout:
            line = raw.rstrip("\n")
            outcome.log_lines.append(line)
            on_line(line)

            warmup = WARMUP_LINE.match(line)
            if warmup:
                on_stage(f"Warmup request {warmup.group(1)}/{warmup.group(2)}", 0.02)
                continue
            users = USERS_LINE.match(line)
            if users:
                done_groups += 1
                progress = min(0.97, 0.05 + 0.92 * done_groups / total_groups)
                remaining = [g for g in groups if g > int(users.group(1))]
                stage = (f"Finished {users.group(1)} concurrent user(s) — "
                         f"next: {remaining[0]} users" if remaining else "Finalizing reports…")
                on_stage(stage, progress)
            elif line.startswith("Benchmarking "):
                on_stage("Connected — running warmup…", 0.02)
            elif line.startswith("Wrote:"):
                on_stage("Writing reports…", 0.99)

        exit_code = self._process.wait()
        if self._managed:
            self._managed.stop()
        outcome.exit_code = exit_code
        outcome.finished_at = time.time()

        if self._cancelled.is_set():
            outcome.status = "cancelled"
            outcome.error = "Cancelled by user."
        elif exit_code == 0:
            outcome.status = "completed"
            on_stage("Done", 1.0)
        else:
            outcome.status = "failed"
            tail = "\n".join(outcome.log_lines[-5:])
            outcome.error = f"Benchmark exited with code {exit_code}.\n{tail}"

        self._write_raw_logs(outcome)
        return outcome

    def _write_raw_logs(self, outcome: RunOutcome) -> None:
        """Always keep the raw log, even for crashes/cancels."""
        try:
            (self.out_dir / "raw_logs.txt").write_text(
                "\n".join(outcome.log_lines) + "\n", encoding="utf-8")
        except OSError:
            pass
