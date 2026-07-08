"""Screen 1 — welcome, system detection, upload transparency."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ...core import system_detect


class DetectWorker(QThread):
    detected = Signal(dict)

    def run(self):
        self.detected.emit(system_detect.detect_all(extended=True))


class SetupScreen(QWidget):
    next_requested = Signal()

    def __init__(self):
        super().__init__()
        self.system_info: dict = {}
        self._worker = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(14)

        title = QLabel("Hardware AI Benchmark")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        subtitle = QLabel(
            "Measure how well this machine serves local AI models: tokens per second, "
            "time to first token, latency, and how many people can chat at once. "
            "Results are saved locally — sharing to the community database is optional and always asks first.")
        subtitle.setWordWrap(True)
        subtitle.setProperty("hint", True)
        outer.addWidget(title)
        outer.addWidget(subtitle)

        # detection card
        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        head = QHBoxLayout()
        card_title = QLabel("Detected system")
        card_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #a898ff;")
        self.refresh_btn = QPushButton("Refresh detection")
        self.refresh_btn.clicked.connect(self.refresh)
        head.addWidget(card_title)
        head.addStretch(1)
        head.addWidget(self.refresh_btn)
        card_layout.addLayout(head)

        self.form_host = QWidget()
        self.form = QFormLayout(self.form_host)
        self.form.setLabelAlignment(Qt.AlignRight)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_host)
        card_layout.addWidget(scroll)
        outer.addWidget(card, 1)

        privacy = QLabel(
            "If you choose to upload a result later, it includes: OS and architecture, CPU model, RAM size, "
            "GPU name and VRAM, runtime/backend, benchmark settings, and the scores. "
            "It never includes file paths, usernames, IP addresses, or environment variables.")
        privacy.setWordWrap(True)
        privacy.setProperty("hint", True)
        outer.addWidget(privacy)

        next_btn = QPushButton("Continue to configuration  →")
        next_btn.setProperty("primary", True)
        next_btn.clicked.connect(self.next_requested.emit)
        outer.addWidget(next_btn, 0, Qt.AlignRight)

        self.refresh()

    def refresh(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Detecting…")
        self._worker = DetectWorker()
        self._worker.detected.connect(self._apply)
        self._worker.start()

    def _apply(self, info: dict):
        self.system_info = info
        while self.form.rowCount():
            self.form.removeRow(0)
        for label, value in system_detect.summarize_for_display(info):
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            key_label = QLabel(label)
            key_label.setProperty("hint", True)
            self.form.addRow(key_label, value_label)
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh detection")
