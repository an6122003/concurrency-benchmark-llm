"""Main window: sidebar step navigation + stacked screens."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QWidget,
)

from ... import APP_NAME, APP_VERSION
from .setup_screen import SetupScreen
from .config_screen import ConfigScreen
from .run_screen import RunScreen
from .results_screen import ResultsScreen

STEPS = ["1  ·  System", "2  ·  Configure", "3  ·  Run", "4  ·  Results"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  ·  v{APP_VERSION}")
        self.resize(1080, 760)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setFixedWidth(190)
        for step in STEPS:
            QListWidgetItem(step, self.nav)
        self.nav.setCurrentRow(0)

        self.stack = QStackedWidget()
        self.setup_screen = SetupScreen()
        self.config_screen = ConfigScreen()
        self.run_screen = RunScreen()
        self.results_screen = ResultsScreen()
        for screen in (self.setup_screen, self.config_screen, self.run_screen, self.results_screen):
            self.stack.addWidget(screen)

        layout.addWidget(self.nav)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        # navigation wiring
        self.nav.currentRowChanged.connect(self._on_nav)
        self.setup_screen.next_requested.connect(lambda: self.go_to(1))
        self.config_screen.run_requested.connect(self._start_run)
        self.run_screen.finished_run.connect(self._show_results)
        self.run_screen.running_changed.connect(self._lock_nav_while_running)
        self.results_screen.new_run_requested.connect(lambda: self.go_to(1))

    # ---------- flow ----------

    def go_to(self, index: int) -> None:
        self.nav.setCurrentRow(index)

    def _on_nav(self, index: int) -> None:
        self.stack.setCurrentIndex(index)

    def _start_run(self, config) -> None:
        self.run_screen.prepare(config, self.setup_screen.system_info)
        self.go_to(2)

    def _show_results(self, bundle) -> None:
        self.results_screen.show_outcome(bundle)
        self.go_to(3)

    def _lock_nav_while_running(self, running: bool) -> None:
        # Freeze config/setup navigation during a run so settings cannot change.
        for row in (0, 1):
            item = self.nav.item(row)
            flag = item.flags()
            item.setFlags(flag & ~Qt.ItemIsEnabled if running else flag | Qt.ItemIsEnabled)

    def closeEvent(self, event) -> None:
        self.run_screen.request_shutdown()
        super().closeEvent(event)
