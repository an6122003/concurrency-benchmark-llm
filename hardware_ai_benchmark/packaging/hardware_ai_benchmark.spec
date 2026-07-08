# PyInstaller spec — build from the repo root:
#   pyinstaller hardware_ai_benchmark/packaging/hardware_ai_benchmark.spec --noconfirm
#
# The benchmark engine (ai_concurrent_benchmark.py) is bundled as DATA so the
# frozen app can re-invoke itself with `--engine` and import it at runtime.

from pathlib import Path

# SPECPATH is the directory containing this spec (…/hardware_ai_benchmark/packaging)
repo = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(repo / "hardware_ai_benchmark" / "packaging" / "entry.py")],
    pathex=[str(repo)],
    datas=[
        (str(repo / "ai_concurrent_benchmark.py"), "."),
        (str(repo / "hardware_ai_benchmark" / "assets"), "hardware_ai_benchmark/assets"),
        # Optional: pre-bundle the built-in llama.cpp runtime so users skip the
        # one-time download. Put llama-server (+ its libs) in <repo>/runtime/
        # before building; otherwise the app offers the download in-UI.
        *([(str(repo / "runtime"), "runtime")] if (repo / "runtime").is_dir() else []),
    ],
    hiddenimports=[],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtCharts", "PySide6.QtQuick",
              "PySide6.QtQml", "PySide6.QtMultimedia"],
    noarchive=False,
)
pyz = PYZ(a.pure)

# Icon formats are platform-specific: .icns (macOS), .ico (Windows), none (Linux).
assets = repo / "hardware_ai_benchmark" / "assets"
if (assets / "icon.icns").exists():
    icon_file = str(assets / "icon.icns")
elif (assets / "icon.ico").exists():
    icon_file = str(assets / "icon.ico")
else:
    icon_file = None

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="HardwareAIBenchmark",
    console=False,
    icon=icon_file,
)
coll = COLLECT(exe, a.binaries, a.datas, name="HardwareAIBenchmark")

app = BUNDLE(
    coll,
    name="Hardware AI Benchmark.app",
    icon=icon_file,
    bundle_identifier="lab.techies.hardware-ai-benchmark",
)
