"""Screen 4 — scores, artifacts, and the consent-first upload dialog."""

from __future__ import annotations

import json
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QThread, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from ...core import uploader as uploader_module
from ...core.result_schema import validate_result


class UploadWorker(QThread):
    done = Signal(object)

    def __init__(self, uploader, payload):
        super().__init__()
        self.uploader = uploader
        self.payload = payload

    def run(self):
        self.done.emit(self.uploader.upload(self.payload))


class UploadDialog(QDialog):
    """Review → consent → upload. Nothing leaves the machine before OK."""

    def __init__(self, document: dict, include_metadata_default: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Share result with the community database")
        self.resize(560, 560)
        self.document = document
        self.worker = None
        settings = QSettings("techies.lab", "HardwareAIBenchmark")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.server_url = QLineEdit(settings.value("upload/server", "http://localhost:8080"))
        self.server_url.setToolTip("The community database server. Leave as-is for the official site.")
        self.alias = QLineEdit(document.get("user_alias") or "")
        self.alias.setPlaceholderText("anonymous")
        self.include_metadata = QCheckBox("Include hardware metadata (GPU, CPU, RAM, OS)")
        self.include_metadata.setChecked(include_metadata_default)
        form.addRow("Server", self.server_url)
        form.addRow("Display name", self.alias)
        layout.addLayout(form)
        layout.addWidget(self.include_metadata)

        layout.addWidget(QLabel("This exact summary will be uploaded:"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview, 1)

        self.consent = QCheckBox("I agree to share this benchmark result and the data shown above.")
        layout.addWidget(self.consent)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.upload_btn = buttons.addButton("Upload", QDialogButtonBox.AcceptRole)
        self.upload_btn.setProperty("primary", True)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._upload)
        layout.addWidget(buttons)

        self.include_metadata.toggled.connect(self._refresh_preview)
        self.alias.textChanged.connect(self._refresh_preview)
        self._refresh_preview()

    def _payload(self) -> dict:
        document = dict(self.document)
        document["user_alias"] = self.alias.text().strip() or None
        return uploader_module.sanitize_for_upload(
            document, include_system_metadata=self.include_metadata.isChecked())

    def _refresh_preview(self):
        payload = self._payload()
        lines = uploader_module.upload_preview(payload)
        derived = (payload.get("results") or {}).get("derived") or {}
        if derived.get("peak_aggregate_tps"):
            lines.insert(1, f"Peak tok/s: {derived['peak_aggregate_tps']} · "
                            f"Comfortable users: {derived.get('comfortable_users', '–')}")
        self.preview.setPlainText("\n".join(lines))

    def _upload(self):
        if not self.consent.isChecked():
            self.status.setText("Please tick the consent box first.")
            return
        payload = self._payload()
        problems = validate_result(payload)
        # sanitization recomputed the checksum; any other problem is a real one
        problems = [p for p in problems if "checksum" not in p]
        if problems:
            self.status.setText("Result failed validation: " + "; ".join(problems))
            return
        QSettings("techies.lab", "HardwareAIBenchmark").setValue("upload/server", self.server_url.text().strip())
        url = self.server_url.text().strip()
        uploader = uploader_module.HttpUploader(url) if url else uploader_module.MockUploader()
        self.upload_btn.setEnabled(False)
        self.status.setText("Uploading…")
        self.worker = UploadWorker(uploader, payload)
        self.worker.done.connect(self._uploaded)
        self.worker.start()

    def _uploaded(self, result):
        self.upload_btn.setEnabled(True)
        self.status.setText(("✓  " if result.ok else "✗  ") + result.message)
        if result.ok:
            self.upload_btn.setText("Uploaded ✓")
            self.upload_btn.setEnabled(False)


class ResultsScreen(QWidget):
    new_run_requested = Signal()

    def __init__(self):
        super().__init__()
        self.bundle: dict = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)
        self.title = QLabel("Results")
        self.title.setStyleSheet("font-size: 22px; font-weight: 700;")
        outer.addWidget(self.title)
        self.status_banner = QLabel("Run a benchmark to see results here.")
        self.status_banner.setWordWrap(True)
        outer.addWidget(self.status_banner)

        self.tiles_host = QFrame(); self.tiles_host.setProperty("card", True)
        self.tiles = QGridLayout(self.tiles_host)
        outer.addWidget(self.tiles_host)

        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setStyleSheet("font-family: Menlo, Consolas, monospace; font-size: 12px;")
        outer.addWidget(self.detail, 1)

        buttons = QHBoxLayout()
        self.open_report = QPushButton("Open HTML report")
        self.open_folder = QPushButton("Open result folder")
        self.export_btn = QPushButton("Export result.json…")
        self.upload_btn = QPushButton("Upload to community database…")
        self.upload_btn.setProperty("primary", True)
        new_run = QPushButton("New run")
        self.open_report.clicked.connect(self._open_report)
        self.open_folder.clicked.connect(self._open_folder)
        self.export_btn.clicked.connect(self._export)
        self.upload_btn.clicked.connect(self.open_upload_dialog)
        new_run.clicked.connect(self.new_run_requested.emit)
        for b in (self.open_report, self.open_folder, self.export_btn, self.upload_btn, new_run):
            buttons.addWidget(b)
        outer.addLayout(buttons)

    # ---------- populate ----------

    def _tile(self, row: int, col: int, label: str, value: str):
        box = QVBoxLayout()
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #65e7c8;")
        key_label = QLabel(label)
        key_label.setProperty("hint", True)
        box.addWidget(value_label)
        box.addWidget(key_label)
        host = QWidget(); host.setLayout(box)
        self.tiles.addWidget(host, row, col)

    def show_outcome(self, bundle: dict) -> None:
        self.bundle = bundle
        outcome = bundle["outcome"]
        document = bundle["document"]
        derived = (document.get("results") or {}).get("derived") or {}

        while self.tiles.count():
            item = self.tiles.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        status = document.get("status")
        if status == "completed":
            self.status_banner.setText(
                f"✓  Benchmark completed in {outcome.duration_s / 60:.1f} minutes. "
                f"Files saved to {outcome.out_dir}")
            self.status_banner.setStyleSheet("color: #65e7c8;")
        elif status == "cancelled":
            self.status_banner.setText(f"⏹  Cancelled. Partial logs kept at {outcome.out_dir}")
            self.status_banner.setStyleSheet("color: #f8c860;")
        else:
            self.status_banner.setText(f"✗  Failed: {outcome.error}")
            self.status_banner.setStyleSheet("color: #ff8080;")

        def fmt(value, suffix=""):
            return f"{value}{suffix}" if value is not None else "–"

        self._tile(0, 0, "Peak aggregate tok/s", fmt(derived.get("peak_aggregate_tps")))
        self._tile(0, 1, "Comfortable users", fmt(derived.get("comfortable_users")))
        self._tile(0, 2, "1-user tok/s", fmt(derived.get("single_user_tps")))
        self._tile(0, 3, "1-user TTFT", fmt(derived.get("ttft_1u_s"), " s"))
        self._tile(0, 4, "Best concurrency", fmt(derived.get("best_concurrency")))

        summaries = (document.get("results") or {}).get("summaries") or []
        lines = [f"Model: {document.get('model', {}).get('name')}   ·   "
                 f"Backend: {bundle['config'].runtime_label or 'auto'}   ·   "
                 f"Status: {status}"]
        for s in summaries:
            lines.append(
                f"users={s.get('concurrency'):>3}  success={s.get('success')}/{s.get('requests')}  "
                f"agg={s.get('aggregate_output_tps')}  per-user={s.get('avg_per_request_tps')}  "
                f"ttft={s.get('avg_ttft_s')}  p95={s.get('p95_latency_s')}")
        lines.append("")
        lines.append("Full raw document in result.json — open the folder to inspect all files.")
        self.detail.setPlainText("\n".join(lines))

        has_report = bool(bundle["artifacts"].get("report.html"))
        self.open_report.setEnabled(has_report)
        self.upload_btn.setEnabled(status == "completed")

        if status == "completed" and bundle["config"].auto_upload:
            self.open_upload_dialog()

    # ---------- actions ----------

    def _open_report(self):
        path = self.bundle.get("artifacts", {}).get("report.html")
        if path:
            webbrowser.open(Path(path).resolve().as_uri())

    def _open_folder(self):
        outcome = self.bundle.get("outcome")
        if outcome and outcome.out_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(outcome.out_dir)))

    def _export(self):
        document = self.bundle.get("document")
        if not document:
            return
        target, _ = QFileDialog.getSaveFileName(self, "Export result.json",
                                                f"result-{document['result_id'][:8]}.json", "JSON (*.json)")
        if target:
            Path(target).write_text(json.dumps(document, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Saved to {target}")

    def open_upload_dialog(self):
        document = self.bundle.get("document")
        if not document:
            return
        config = self.bundle.get("config")
        dialog = UploadDialog(document, config.include_metadata_in_upload if config else True, self)
        dialog.exec()
