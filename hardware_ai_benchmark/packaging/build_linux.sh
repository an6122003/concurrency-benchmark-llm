#!/usr/bin/env bash
# Build the Linux app (Ubuntu/Debian first). Run from the repo root:
#   python3.12 -m venv .venv-gui && .venv-gui/bin/pip install PySide6 pyinstaller
#   bash hardware_ai_benchmark/packaging/build_linux.sh
#
# System packages PySide6 may need at runtime on minimal distros:
#   sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libegl1
set -euo pipefail
cd "$(dirname "$0")/../.."

PYTHON="${PYTHON:-.venv-gui/bin/python}"
"$PYTHON" -m PyInstaller hardware_ai_benchmark/packaging/hardware_ai_benchmark.spec \
  --noconfirm --distpath dist --workpath build

echo
echo "Built: dist/HardwareAIBenchmark/ (portable folder — run ./HardwareAIBenchmark)"
echo "AppImage (optional): package dist/HardwareAIBenchmark with appimagetool;"
echo "a .desktop file and the icon from hardware_ai_benchmark/assets are required."
