"""Configure-screen panel for the built-in runtime: install llama.cpp and
pick/download a benchmark model from the curated catalog."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QProgressBar, QPushButton, QRadioButton, QVBoxLayout, QWidget,
)

from ...core import model_catalog, runtime_manager


def _detected_ram_gb() -> Optional[float]:
    try:
        from ...core import engine
        info = engine.load_engine().collect_memory_info()
        total = info.get("total_bytes")
        return total / (1024 ** 3) if total else None
    except Exception:
        return None


class DownloadWorker(QThread):
    """Runs one download function off the UI thread."""
    progress = Signal(int, int)          # bytes done, bytes total
    finished_with = Signal(str)          # error message; empty on success

    def __init__(self, job: Callable[..., object]):
        super().__init__()
        self._job = job
        self.cancel_event = threading.Event()

    def run(self):
        try:
            self._job(on_progress=self.progress.emit, cancel=self.cancel_event)
            self.finished_with.emit("")
        except OSError as exc:
            self.finished_with.emit(str(exc))


class BuiltinRuntimePanel(QFrame):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.setProperty("card", True)
        self._ram_gb = _detected_ram_gb()
        self._worker: Optional[DownloadWorker] = None
        self._model_buttons: dict[str, tuple[QRadioButton, QPushButton, QLabel]] = {}

        layout = QVBoxLayout(self)

        # ---- runtime install status ----
        runtime_row = QHBoxLayout()
        self.runtime_status = QLabel("")
        self.install_btn = QPushButton("Download runtime")
        self.install_btn.setToolTip(
            "Fetches the official llama.cpp server for this machine (~10–30 MB). One-time.")
        self.install_btn.clicked.connect(self._install_runtime)
        runtime_row.addWidget(self.runtime_status, 1)
        runtime_row.addWidget(self.install_btn)
        layout.addLayout(runtime_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        hint = QLabel("Pick a model — it downloads once, then everything runs on this machine. "
                      "Bigger models are harder work for your hardware and score lower but "
                      "test it more meaningfully.")
        hint.setProperty("hint", True)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ---- model catalog ----
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        self.model_group = QButtonGroup(self)
        for row, model in enumerate(model_catalog.CATALOG):
            radio = QRadioButton(f"{model.name}  ·  {model.quantization}  ·  {model.size_mb / 1024:.1f} GB"
                                 if model.size_mb >= 1024 else
                                 f"{model.name}  ·  {model.quantization}  ·  {model.size_mb} MB")
            radio.setToolTip(f"{model.blurb}  License: {model.license}.")
            radio.toggled.connect(lambda *_: self.changed.emit())
            self.model_group.addButton(radio)
            fit = QLabel(model_catalog.fit_hint(model, self._ram_gb))
            fit.setProperty("warning", True)
            action = QPushButton()
            action.setFixedWidth(130)
            action.clicked.connect(lambda _, m=model: self._download_model(m))
            grid.addWidget(radio, row, 0)
            grid.addWidget(fit, row, 1)
            grid.addWidget(action, row, 2)
            self._model_buttons[model.key] = (radio, action, fit)

        # custom GGUF row
        custom_row = len(model_catalog.CATALOG)
        self.custom_radio = QRadioButton("Custom GGUF file")
        self.custom_radio.setToolTip("Benchmark any .gguf model you already have on disk.")
        self.custom_radio.toggled.connect(lambda *_: self.changed.emit())
        self.model_group.addButton(self.custom_radio)
        custom_picker = QWidget()
        picker_layout = QHBoxLayout(custom_picker)
        picker_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_path = QLineEdit()
        self.custom_path.setPlaceholderText("path to a .gguf file")
        self.custom_path.textChanged.connect(lambda *_: self.changed.emit())
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._pick_custom)
        picker_layout.addWidget(self.custom_path, 1)
        picker_layout.addWidget(browse)
        grid.addWidget(self.custom_radio, custom_row, 0)
        grid.addWidget(custom_picker, custom_row, 1, 1, 2)
        layout.addLayout(grid)

        self.status = QLabel("")
        self.status.setProperty("hint", True)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.refresh()

    # ---------- state ----------

    def refresh(self) -> None:
        installed = runtime_manager.is_installed()
        self.runtime_status.setText(
            f"✓ Runtime installed ({runtime_manager.installed_description()})" if installed
            else "Runtime not installed — download it once to run models in-app.")
        self.install_btn.setVisible(not installed)
        for key, (radio, action, _fit) in self._model_buttons.items():
            model = model_catalog.by_key(key)
            if model_catalog.is_downloaded(model):
                action.setText("✓ Downloaded")
                action.setEnabled(False)
                if self.model_group.checkedButton() is None:
                    radio.setChecked(True)
            else:
                action.setText("Download")
                action.setEnabled(self._worker is None)
        self.changed.emit()

    def is_busy(self) -> bool:
        return self._worker is not None

    def is_ready(self) -> tuple[bool, str]:
        """(ready, reason-if-not) for the Continue button."""
        if not runtime_manager.is_installed():
            return False, "Download the runtime first (one-time, ~10–30 MB)."
        if self._worker is not None:
            return False, "Wait for the current download to finish."
        if self.selection() is None:
            return False, "Pick a downloaded model, or download one."
        return True, ""

    def selection(self) -> Optional[dict]:
        """{'file','name','quantization'} for the checked model, else None."""
        if self.custom_radio.isChecked():
            path = Path(self.custom_path.text().strip())
            if path.suffix == ".gguf" and path.exists():
                return {"file": str(path), "name": path.stem, "quantization": ""}
            return None
        for key, (radio, _action, _fit) in self._model_buttons.items():
            model = model_catalog.by_key(key)
            if radio.isChecked() and model_catalog.is_downloaded(model):
                return {"file": str(model_catalog.local_path(model)),
                        "name": model.name, "quantization": model.quantization}
        return None

    # ---------- downloads ----------

    def _start_worker(self, job: Callable[..., object], label: str) -> None:
        if self._worker is not None:
            return
        self._worker = DownloadWorker(job)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_with.connect(lambda err, lbl=label: self._on_done(err, lbl))
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status.setText(f"Downloading {label}…")
        self.install_btn.setEnabled(False)
        for _radio, action, _fit in self._model_buttons.values():
            action.setEnabled(False)
        self._worker.start()

    def _install_runtime(self) -> None:
        self._start_worker(runtime_manager.install_runtime, "runtime")

    def _download_model(self, model) -> None:
        self._start_worker(
            lambda on_progress, cancel: model_catalog.download(model, on_progress, cancel),
            model.name)

    def _on_progress(self, done: int, total: int) -> None:
        if total:
            self.progress.setValue(int(done / total * 1000))
            self.status.setText(
                f"Downloading… {done / 1048576:.0f} / {total / 1048576:.0f} MB")

    def _on_done(self, error: str, label: str) -> None:
        self._worker = None
        self.progress.setVisible(False)
        self.install_btn.setEnabled(True)
        self.status.setText(f"Could not download {label}: {error}" if error
                            else f"{label} ready.")
        self.refresh()

    def _pick_custom(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose a GGUF model", "", "GGUF models (*.gguf)")
        if path:
            self.custom_path.setText(path)
            self.custom_radio.setChecked(True)

    def request_shutdown(self) -> None:
        if self._worker is not None:
            self._worker.cancel_event.set()
            self._worker.wait(3000)
