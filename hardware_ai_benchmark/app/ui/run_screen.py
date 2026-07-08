"""Screen 3 — the Run button, live progress, logs, cancel."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

from ...core.benchmark_runner import BenchmarkRunner, RunOutcome
from ...core.config import BenchmarkConfig
from ...core import report_generator, result_schema


class RunWorker(QThread):
    line = Signal(str)
    stage = Signal(str, float)
    done = Signal(object)   # RunOutcome

    def __init__(self, runner: BenchmarkRunner):
        super().__init__()
        self.runner = runner

    def run(self):
        outcome = self.runner.run(
            on_line=self.line.emit,
            on_stage=self.stage.emit,
        )
        self.done.emit(outcome)


class RunScreen(QWidget):
    finished_run = Signal(dict)          # bundle for the results screen
    running_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.config: BenchmarkConfig | None = None
        self.system_info: dict = {}
        self.runner: BenchmarkRunner | None = None
        self.worker: RunWorker | None = None
        self._started_at = 0.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        title = QLabel("Run benchmark")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        outer.addWidget(title)

        self.summary = QLabel("")
        self.summary.setProperty("hint", True)
        self.summary.setWordWrap(True)
        outer.addWidget(self.summary)

        card = QFrame(); card.setProperty("card", True)
        card_layout = QVBoxLayout(card)

        controls = QHBoxLayout()
        self.run_btn = QPushButton("▶   Run Benchmark")
        self.run_btn.setProperty("primary", True)
        self.run_btn.setMinimumHeight(46)
        self.run_btn.clicked.connect(self.start)
        self.cancel_btn = QPushButton("Stop")
        self.cancel_btn.setProperty("danger", True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel)
        self.elapsed = QLabel("")
        self.elapsed.setProperty("hint", True)
        controls.addWidget(self.run_btn, 1)
        controls.addWidget(self.cancel_btn)
        controls.addWidget(self.elapsed)
        card_layout.addLayout(controls)

        self.stage_label = QLabel("Ready.")
        card_layout.addWidget(self.stage_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        card_layout.addWidget(self.progress)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        self.log_view.setStyleSheet("font-family: Menlo, Consolas, monospace; font-size: 12px;")
        card_layout.addWidget(self.log_view, 1)
        outer.addWidget(card, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    # ---------- lifecycle ----------

    def prepare(self, config: BenchmarkConfig, system_info: dict) -> None:
        self.config = config
        self.system_info = system_info
        self.summary.setText(
            f"Model {config.model}  ·  {config.server} at {config.base_url}  ·  "
            f"users {config.concurrency}  ·  {config.max_tokens} tokens/request  ·  preset: {config.preset}")
        self.stage_label.setText("Ready. Press Run Benchmark to start.")
        self.progress.setValue(0)
        self.log_view.clear()
        self.run_btn.setEnabled(True)

    def start(self) -> None:
        if not self.config or self.worker:
            return
        self.runner = BenchmarkRunner(self.config)
        self.worker = RunWorker(self.runner)
        self.worker.line.connect(self._append_line)
        self.worker.stage.connect(self._set_stage)
        self.worker.done.connect(self._finished)
        self._started_at = time.time()
        self._timer.start()
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.running_changed.emit(True)
        self.worker.start()

    def cancel(self) -> None:
        if self.runner:
            self.stage_label.setText("Stopping…")
            self.cancel_btn.setEnabled(False)
            self.runner.cancel()

    def request_shutdown(self) -> None:
        if self.runner:
            self.runner.cancel()

    # ---------- slots ----------

    def _append_line(self, line: str) -> None:
        self.log_view.appendPlainText(line)

    def _set_stage(self, stage: str, progress: float) -> None:
        self.stage_label.setText(stage)
        self.progress.setValue(int(progress * 1000))

    def _tick(self) -> None:
        seconds = int(time.time() - self._started_at)
        self.elapsed.setText(f"{seconds // 60:02d}:{seconds % 60:02d} elapsed")

    def _finished(self, outcome: RunOutcome) -> None:
        self._timer.stop()
        self.cancel_btn.setEnabled(False)
        self.run_btn.setEnabled(True)
        self.running_changed.emit(False)
        self.worker = None

        # Build the canonical result document even for failures/cancels,
        # so partial logs and status are preserved.
        engine_results = report_generator.load_engine_results(outcome.out_dir) if outcome.out_dir else None
        document = result_schema.build_result(
            self.config, self.system_info, engine_results,
            status=outcome.status,
            errors=[outcome.error] if outcome.error else [],
            warnings=self.config.warnings(),
        )
        artifacts = report_generator.write_result_files(outcome.out_dir, document) if outcome.out_dir else {}

        self.finished_run.emit({
            "outcome": outcome,
            "document": document,
            "artifacts": artifacts,
            "config": self.config,
        })
