#!/usr/bin/env bash
# Build the macOS app bundle. Run from the repo root with a Python 3.10–3.13 venv:
#   python3.12 -m venv .venv-gui && .venv-gui/bin/pip install PySide6 pyinstaller
#   bash hardware_ai_benchmark/packaging/build_macos.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PYTHON="${PYTHON:-.venv-gui/bin/python}"
"$PYTHON" -m PyInstaller hardware_ai_benchmark/packaging/hardware_ai_benchmark.spec \
  --noconfirm --distpath dist --workpath build

echo
echo "Built: dist/Hardware AI Benchmark.app"
echo "Note: unsigned. For distribution, codesign + notarize:"
echo "  codesign --deep --force --sign 'Developer ID Application: ...' 'dist/Hardware AI Benchmark.app'"
echo "  xcrun notarytool submit ... (see Apple docs)"
echo "Create a DMG (optional): hdiutil create -volname 'Hardware AI Benchmark' -srcfolder 'dist/Hardware AI Benchmark.app' -ov -format UDZO dist/HardwareAIBenchmark.dmg"
