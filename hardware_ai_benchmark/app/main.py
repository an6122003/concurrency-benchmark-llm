"""Qt application bootstrap with the Techies Lab dark theme."""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .. import APP_NAME
from ..core.logger import get_logger
from ..core.paths import repo_root

STYLESHEET = """
* { font-family: "Inter", "Segoe UI", -apple-system, sans-serif; }
QMainWindow, QDialog { background: #0a0918; }
QWidget { color: #ecebf5; font-size: 13px; }
QLabel[hint="true"] { color: #8d8ba6; }
QLabel[error="true"] { color: #ff8080; }
QLabel[warning="true"] { color: #f8c860; }

QFrame[card="true"] {
  background: rgba(21, 19, 42, 0.75);
  border: 1px solid rgba(138, 112, 255, 0.22);
  border-radius: 10px;
}

QPushButton {
  background: rgba(28, 25, 54, 0.9);
  border: 1px solid rgba(138, 112, 255, 0.35);
  border-radius: 8px;
  padding: 8px 16px;
}
QPushButton:hover { border-color: #a898ff; background: rgba(138, 112, 255, 0.18); }
QPushButton:disabled { color: #5f5d78; border-color: rgba(138, 112, 255, 0.12); }
QPushButton[primary="true"] {
  background: #7a62f0;
  border: 1px solid #a898ff;
  color: white;
  font-weight: 600;
}
QPushButton[primary="true"]:hover { background: #8a70ff; }
QPushButton[primary="true"]:disabled { background: #3a3556; color: #8d8ba6; }
QPushButton[danger="true"] { border-color: rgba(255, 128, 128, 0.5); }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
  background: rgba(14, 13, 31, 0.9);
  border: 1px solid rgba(138, 112, 255, 0.3);
  border-radius: 7px;
  padding: 6px 9px;
  selection-background-color: #7a62f0;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #a898ff; }
QComboBox::drop-down { border: 0; width: 22px; }
QComboBox QAbstractItemView { background: #15132a; border: 1px solid #4b3f8f; }

QProgressBar {
  background: rgba(14, 13, 31, 0.9);
  border: 1px solid rgba(138, 112, 255, 0.3);
  border-radius: 8px;
  height: 18px;
  text-align: center;
  color: white;
}
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a70ff, stop:1 #62d6ff); border-radius: 7px; }

QListWidget {
  background: rgba(14, 13, 31, 0.7);
  border: 0;
  border-right: 1px solid rgba(138, 112, 255, 0.18);
  padding-top: 8px;
}
QListWidget::item { padding: 12px 18px; border-radius: 8px; margin: 2px 8px; }
QListWidget::item:selected { background: rgba(138, 112, 255, 0.22); color: white; }

QCheckBox, QRadioButton { spacing: 8px; }
QGroupBox {
  border: 1px solid rgba(138, 112, 255, 0.22);
  border-radius: 10px;
  margin-top: 12px;
  padding-top: 10px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #a898ff; }
QScrollArea { border: 0; }
QTabWidget::pane { border: 0; }
"""


def run() -> int:
    logger = get_logger()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLESHEET)

    icon_path = repo_root() / "hardware_ai_benchmark" / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from .ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    logger.info("app started")

    # Headless smoke-test mode used by CI/dev checks.
    if os.environ.get("HAB_SMOKE_TEST"):
        QTimer.singleShot(1500, app.quit)

    return app.exec()
