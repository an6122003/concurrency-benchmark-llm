@echo off
REM Build the Windows app. Run from the repo root with a Python 3.10-3.13 venv:
REM   py -3.12 -m venv .venv-gui
REM   .venv-gui\Scripts\pip install PySide6 pyinstaller
REM   hardware_ai_benchmark\packaging\build_windows.bat
cd /d "%~dp0..\.."

set PYTHON=.venv-gui\Scripts\python.exe
if not exist %PYTHON% set PYTHON=python

%PYTHON% -m PyInstaller hardware_ai_benchmark\packaging\hardware_ai_benchmark.spec --noconfirm --distpath dist --workpath build
if errorlevel 1 exit /b 1

echo.
echo Built: dist\HardwareAIBenchmark\HardwareAIBenchmark.exe
echo Zip that folder for distribution, or wrap it with Inno Setup / NSIS for an installer.
