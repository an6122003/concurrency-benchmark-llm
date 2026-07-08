"""Screen 2 — presets, beginner fields, advanced options, live warnings."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton,
    QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from ...core.config import BenchmarkConfig
from ...core import system_detect
from .builtin_runtime_panel import BuiltinRuntimePanel

PRESET_LABELS = {
    "quick": "Quick Test",
    "standard": "Standard Test",
    "full": "Full Test",
    "stress": "Stress Test",
}


class ConfigScreen(QWidget):
    run_requested = Signal(object)   # BenchmarkConfig

    def __init__(self):
        super().__init__()
        self._preset_name = "standard"
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        title = QLabel("Configure the benchmark")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setSpacing(12)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        # ---- presets ----
        preset_card = QFrame(); preset_card.setProperty("card", True)
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.addWidget(self._section_label("Choose a test size"))
        row = QHBoxLayout()
        self.preset_group = QButtonGroup(self)
        self.preset_hint = QLabel("")
        self.preset_hint.setProperty("hint", True)
        self._preset_buttons = {}
        for name, config in BenchmarkConfig.presets().items():
            button = QRadioButton(PRESET_LABELS[name])
            button.setToolTip(config.preset_hint)
            button.toggled.connect(lambda checked, n=name: checked and self._apply_preset(n))
            self.preset_group.addButton(button)
            row.addWidget(button)
            self._preset_buttons[name] = button
        row.addStretch(1)
        preset_layout.addLayout(row)
        preset_layout.addWidget(self.preset_hint)
        layout.addWidget(preset_card)

        # ---- where the model runs ----
        mode_card = QFrame(); mode_card.setProperty("card", True)
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.addWidget(self._section_label("Where should the model run?"))
        mode_row = QHBoxLayout()
        self.mode_builtin = QRadioButton("Built-in runtime (recommended)")
        self.mode_builtin.setToolTip(
            "The app downloads a model and runs it itself with llama.cpp — nothing else to install.")
        self.mode_server = QRadioButton("My own server (LM Studio / Ollama)")
        self.mode_server.setToolTip("Benchmark a model already loaded in LM Studio or Ollama.")
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.mode_builtin)
        mode_group.addButton(self.mode_server)
        mode_row.addWidget(self.mode_builtin)
        mode_row.addWidget(self.mode_server)
        mode_row.addStretch(1)
        mode_layout.addLayout(mode_row)
        layout.addWidget(mode_card)

        # ---- built-in runtime ----
        self.builtin_panel = BuiltinRuntimePanel()
        self.builtin_panel.changed.connect(self._refresh_warnings)
        layout.addWidget(self.builtin_panel)

        # ---- connection ----
        conn_card = QFrame(); conn_card.setProperty("card", True)
        self.conn_card = conn_card
        conn_layout = QFormLayout(conn_card)
        self.server = QComboBox()
        self.server.addItems(["lmstudio", "ollama", "ollama-native"])
        self.server.setToolTip("Which local AI server is running your model.")
        self.base_url = QLineEdit("http://localhost:1234")
        self.base_url.setToolTip("Where the server listens. LM Studio: 1234 · Ollama: 11434.")
        self.server.currentTextChanged.connect(self._default_url)
        model_row = QWidget(); model_layout = QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        self.model = QComboBox(); self.model.setEditable(True)
        self.model.setToolTip("The model to benchmark — must already be loaded/pulled in your server.")
        detect_models = QPushButton("Find models")
        detect_models.setToolTip("Ask the server which models it has.")
        detect_models.clicked.connect(self._find_models)
        model_layout.addWidget(self.model, 1); model_layout.addWidget(detect_models)
        conn_layout.addRow("AI server", self.server)
        conn_layout.addRow("Server URL", self.base_url)
        conn_layout.addRow("Model", model_row)
        layout.addWidget(conn_card)

        # ---- advanced ----
        self.advanced = QGroupBox("Advanced settings")
        self.advanced.setCheckable(True)
        self.advanced.setChecked(False)
        adv = QFormLayout(self.advanced)
        self.concurrency = QLineEdit("1-8"); self.concurrency.setToolTip("User counts to simulate, e.g. 1-8 or 1,2,4,8.")
        self.max_tokens = QSpinBox(); self.max_tokens.setRange(1, 8192); self.max_tokens.setValue(256)
        self.max_tokens.setToolTip("Generated tokens per request. More tokens = longer, steadier measurement.")
        self.temperature = QDoubleSpinBox(); self.temperature.setRange(0, 2); self.temperature.setSingleStep(0.1); self.temperature.setValue(0.2)
        self.timeout = QSpinBox(); self.timeout.setRange(30, 3600); self.timeout.setValue(600); self.timeout.setSuffix(" s")
        self.warmup = QSpinBox(); self.warmup.setRange(0, 5); self.warmup.setValue(1)
        self.warmup.setToolTip("Unmeasured request(s) first, so model loading doesn't hurt the 1-user score.")
        self.quantization = QLineEdit(); self.quantization.setPlaceholderText("auto-detected when possible, e.g. Q4_K_M")
        self.context_size = QSpinBox(); self.context_size.setRange(0, 1_000_000); self.context_size.setSpecialValueText("auto")
        self.gpu_label = QLineEdit(); self.gpu_label.setPlaceholderText("optional label, e.g. RTX 4090 24GB")
        self.runtime_label = QLineEdit(); self.runtime_label.setPlaceholderText("optional, e.g. Vulkan llama.cpp")
        self.notes = QLineEdit(); self.notes.setPlaceholderText("optional notes stored with the result")
        out_row = QWidget(); out_layout = QHBoxLayout(out_row); out_layout.setContentsMargins(0, 0, 0, 0)
        self.out_dir = QLineEdit(); self.out_dir.setPlaceholderText("auto: Documents/HardwareAIBenchmark/run-<date>")
        browse = QPushButton("Browse…"); browse.clicked.connect(self._pick_out_dir)
        out_layout.addWidget(self.out_dir, 1); out_layout.addWidget(browse)
        for label, widget in [
            ("Concurrency", self.concurrency), ("Max tokens", self.max_tokens),
            ("Temperature", self.temperature), ("Timeout", self.timeout),
            ("Warmup runs", self.warmup), ("Quantization", self.quantization),
            ("Context size", self.context_size), ("GPU label", self.gpu_label),
            ("Runtime label", self.runtime_label), ("Notes", self.notes),
            ("Output folder", out_row),
        ]:
            adv.addRow(label, widget)
        layout.addWidget(self.advanced)

        # ---- sharing ----
        share_card = QFrame(); share_card.setProperty("card", True)
        share_layout = QVBoxLayout(share_card)
        share_layout.addWidget(self._section_label("Saving and sharing"))
        self.extended_info = QCheckBox("Collect extended system information (GPU/VRAM details)")
        self.extended_info.setChecked(True)
        self.include_metadata = QCheckBox("Include anonymous hardware metadata if I upload")
        self.include_metadata.setChecked(True)
        self.auto_upload = QCheckBox("Offer to upload right after the run finishes")
        self.alias = QLineEdit(); self.alias.setPlaceholderText("optional display name for the leaderboard")
        share_layout.addWidget(self.extended_info)
        share_layout.addWidget(self.include_metadata)
        share_layout.addWidget(self.auto_upload)
        alias_row = QFormLayout(); alias_row.addRow("Display name", self.alias)
        share_layout.addLayout(alias_row)
        layout.addWidget(share_card)
        layout.addStretch(1)

        # ---- footer: warnings + run ----
        self.problems = QLabel("")
        self.problems.setWordWrap(True)
        outer.addWidget(self.problems)
        run_btn = QPushButton("Continue to Run  →")
        run_btn.setProperty("primary", True)
        run_btn.clicked.connect(self._submit)
        outer.addWidget(run_btn, 0, Qt.AlignRight)

        for widget in (self.concurrency, self.base_url):
            widget.textChanged.connect(self._refresh_warnings)
        self.max_tokens.valueChanged.connect(self._refresh_warnings)
        self.context_size.valueChanged.connect(self._refresh_warnings)
        self.warmup.valueChanged.connect(self._refresh_warnings)
        # All widgets exist now; checking the defaults applies them.
        self.mode_builtin.toggled.connect(self._apply_mode)
        self.mode_builtin.setChecked(True)
        self._apply_mode()
        self._preset_buttons["standard"].setChecked(True)

    # ---------- helpers ----------

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 15px; font-weight: 600; color: #a898ff;")
        return label

    def _default_url(self, server: str) -> None:
        self.base_url.setText("http://localhost:11434" if server.startswith("ollama") else "http://localhost:1234")

    def _apply_mode(self, *_args) -> None:
        builtin = self.mode_builtin.isChecked()
        self.builtin_panel.setVisible(builtin)
        self.conn_card.setVisible(not builtin)
        self._refresh_warnings()

    def request_shutdown(self) -> None:
        self.builtin_panel.request_shutdown()

    def _apply_preset(self, name: str) -> None:
        preset = BenchmarkConfig.presets()[name]
        self._preset_name = name
        self.preset_hint.setText(preset.preset_hint)
        self.concurrency.setText(preset.concurrency)
        self.max_tokens.setValue(preset.max_tokens)
        self.warmup.setValue(preset.warmup)
        self.timeout.setValue(int(preset.timeout_s))
        self._refresh_warnings()

    def _pick_out_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if path:
            self.out_dir.setText(path)

    def _find_models(self) -> None:
        models = system_detect.list_server_models(self.server.currentText(), self.base_url.text().strip())
        current = self.model.currentText()
        self.model.clear()
        self.model.addItems(models)
        if current:
            self.model.setCurrentText(current)
        elif not models:
            self.problems.setProperty("warning", True)
            self.problems.setText("No models reported — is the server running at that URL?")
            self.problems.style().polish(self.problems)

    def collect(self) -> BenchmarkConfig:
        builtin = self.mode_builtin.isChecked()
        selection = self.builtin_panel.selection() if builtin else None
        return BenchmarkConfig(
            server="lmstudio" if builtin else self.server.currentText(),
            base_url=self.base_url.text().strip(),
            use_builtin_runtime=builtin,
            model_file=(selection or {}).get("file", ""),
            model=(selection or {}).get("name", "") if builtin else self.model.currentText().strip(),
            concurrency=self.concurrency.text().strip(),
            max_tokens=self.max_tokens.value(),
            temperature=self.temperature.value(),
            timeout_s=float(self.timeout.value()),
            warmup=self.warmup.value(),
            quantization=self.quantization.text().strip() or (selection or {}).get("quantization", ""),
            context_size=self.context_size.value() or None,
            gpu_label=self.gpu_label.text().strip(),
            runtime_label=self.runtime_label.text().strip() or ("llama.cpp (built-in)" if builtin else ""),
            notes=self.notes.text().strip(),
            out_dir=self.out_dir.text().strip(),
            preset=self._preset_name,
            collect_extended_info=self.extended_info.isChecked(),
            include_metadata_in_upload=self.include_metadata.isChecked(),
            auto_upload=self.auto_upload.isChecked(),
            user_alias=self.alias.text().strip(),
        )

    def _refresh_warnings(self) -> None:
        config = self.collect()
        warns = config.warnings()
        if warns:
            self.problems.setProperty("error", False)
            self.problems.setProperty("warning", True)
            self.problems.setText("⚠  " + "\n⚠  ".join(warns))
        else:
            self.problems.setText("")
        self.problems.style().polish(self.problems)

    def _submit(self) -> None:
        if self.mode_builtin.isChecked():
            ready, reason = self.builtin_panel.is_ready()
            if not ready:
                self.problems.setProperty("warning", False)
                self.problems.setProperty("error", True)
                self.problems.setText("✗  " + reason)
                self.problems.style().polish(self.problems)
                return
        config = self.collect()
        errors = config.validate()
        if errors:
            self.problems.setProperty("warning", False)
            self.problems.setProperty("error", True)
            self.problems.setText("✗  " + "\n✗  ".join(errors))
            self.problems.style().polish(self.problems)
            return
        self.run_requested.emit(config)
