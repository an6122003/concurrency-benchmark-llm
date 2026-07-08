# Hardware AI Benchmark — desktop app

A one-button desktop app that wraps the Techies Lab concurrent LLM benchmark
(`ai_concurrent_benchmark.py`) so non-technical users can test their AI
hardware and optionally share results with the community database website in
this repo.

**Flow:** detect system → pick a preset → Run Benchmark → live progress and
logs → automatic reports → review-and-consent upload.

---

## For end users

1. Start your local AI server (LM Studio or Ollama) and load a model.
2. Open **Hardware AI Benchmark**.
3. **System** — check the detected hardware; press *Refresh detection* if you
   changed anything.
4. **Configure** — pick a test size:
   - **Quick Test** ~3–5 min: fast sanity check
   - **Standard Test** ~10–20 min: the recommended community test
   - **Full Test** ~30–60 min: full concurrency sweep
   - **Stress Test** 1h+: pushes queueing and memory limits
   Press *Find models* to pick from what your server has loaded. Advanced
   settings are hidden unless you open them.
5. **Run** — press *Run Benchmark*. You can watch stage, progress, elapsed
   time and live logs, or press *Stop* at any time (partial logs are kept).
6. **Results** — see your scores, open the visual HTML report, or press
   *Upload to community database*. Uploading always shows you exactly what
   will be sent and requires a consent checkbox. Anonymous by default.

Results are saved to `Documents/HardwareAIBenchmark/run-<date>/` with:

| File | What it is |
| --- | --- |
| `result.json` | canonical structured result (schema v1, checksummed) |
| `report.html` | visual report with charts, good for sharing |
| `report.md` | readable text summary |
| `results.json` / `results.csv` | raw engine output |
| `metadata.json` / `app_metadata.json` | system + app/version metadata |
| `raw_logs.txt` | full log output, kept even on crash/cancel |

### Privacy

- Nothing is uploaded without pressing Upload and ticking consent.
- Uploads never include file paths, usernames, IPs/URLs, or environment
  variables; home-directory strings are scrubbed.
- You can withhold hardware metadata entirely with one checkbox.
- The anonymous machine id is a random token, not derived from your hardware.
- Failed uploads are kept in a local outbox and can be retried.

---

## For developers

```bash
# run the app (any Python 3.10–3.13 with PySide6)
python3.12 -m venv .venv-gui
.venv-gui/bin/pip install PySide6
.venv-gui/bin/python -m hardware_ai_benchmark

# run core tests (stdlib only, any Python 3.10+)
python3 -m unittest discover -s hardware_ai_benchmark/tests

# headless GUI smoke test
HAB_SMOKE_TEST=1 QT_QPA_PLATFORM=offscreen .venv-gui/bin/python -m hardware_ai_benchmark
```

### Architecture

```
hardware_ai_benchmark/
  __main__.py         entry; `--engine` dispatches to the benchmark engine
  app/                Qt layer (PySide6) — no benchmark logic here
    main.py           QApplication + theme
    ui/               main_window + 4 screens (setup/config/run/results)
  core/               UI-independent, stdlib-only
    engine.py         locates/imports ai_concurrent_benchmark.py
    config.py         BenchmarkConfig: presets, validation, warnings, CLI args
    system_detect.py  platform/arch/backends + engine's hardware collectors
    benchmark_runner.py  subprocess runner, stdout→progress, cancel, crash logs
    result_schema.py  schema v1: build, validate, checksum, derived scores
    report_generator.py  result.json + app_metadata.json next to engine files
    uploader.py       sanitize → Mock (outbox) / Http (POST /api/benchmark-results)
    paths.py          AppData / Application Support / XDG locations
  packaging/          PyInstaller spec + per-OS build scripts
  tests/              unittest suite for config/schema/reports/uploader/detect
```

Key decisions:

- **The engine is untouched.** The app runs it as a child process and parses
  its stdout (`warmup i/N`, `users=N success=...`) for stage/progress. In a
  frozen build the app re-invokes itself with `--engine` since there is no
  system Python.
- **Core is stdlib-only** (dataclasses + explicit validation instead of
  pydantic) so tests run anywhere and the packaged app stays small. The
  schema module is the single swap-in point if pydantic is wanted later.
- **Uploads hit the community server in this repo**:
  `POST /api/benchmark-results` (see `server/app.py`) stores the document
  under `data/uploads/` and imports a browsable run into the database. With
  no server configured, the MockUploader saves payloads to a local outbox;
  the outbox doubles as the retry queue.

### Versioning

`hardware_ai_benchmark/__init__.py` defines `APP_VERSION`,
`BENCHMARK_SUITE_VERSION`, and `SCHEMA_VERSION`. Bump `SCHEMA_VERSION` on any
breaking change to `result.json`; the server can then branch on it.

---

## Packaging

```bash
# macOS (current dev OS) — produces "dist/Hardware AI Benchmark.app"
bash hardware_ai_benchmark/packaging/build_macos.sh

# Windows — produces dist\HardwareAIBenchmark\HardwareAIBenchmark.exe
hardware_ai_benchmark\packaging\build_windows.bat

# Linux — produces a portable dist/HardwareAIBenchmark/ folder
bash hardware_ai_benchmark/packaging/build_linux.sh
```

All three use the same PyInstaller spec
(`packaging/hardware_ai_benchmark.spec`), which bundles the engine script and
assets. Users need no Python install.

### Platform compatibility matrix

| Platform | Status | Package type | Notes |
| --- | --- | --- | --- |
| Windows 10/11 | Target MVP | portable .exe folder (installer via Inno/NSIS later) | primary desktop support |
| macOS Apple Silicon | Target MVP | .app (optional .dmg via hdiutil) | built/tested on this repo's dev machine |
| macOS Intel | Best effort | .app | build on an Intel Mac or `--target-arch x86_64` if deps allow |
| Linux Ubuntu/Debian | Target MVP | portable folder (AppImage optional) | needs `libxcb-cursor0 libxkbcommon-x11-0 libegl1` on minimal installs |
| Other Linux | Best effort | AppImage | untested |
| Android | Experimental | — | see feasibility below; not part of the desktop MVP |

### Troubleshooting

**All platforms**
- "Model is required" — press *Find models*; your server must be running with
  a model loaded.
- Benchmark fails instantly — verify the URL on the Configure screen
  (LM Studio `http://localhost:1234`, Ollama `http://localhost:11434`).
- App logs live in the platform data dir (`logs/app.log`), results in
  `Documents/HardwareAIBenchmark/`.

**Windows** — SmartScreen may warn on unsigned builds: *More info → Run
anyway*. Real distribution needs code signing.

**macOS** — first launch of an unsigned app: right-click → *Open*. Signing +
notarization are documented in `build_macos.sh` as a production step.

**Linux** — if the window doesn't appear on Wayland, try
`QT_QPA_PLATFORM=xcb`. Install the apt packages listed in `build_linux.sh`.

---

## Android feasibility (experimental — do not block desktop MVP)

The benchmark measures a **local LLM server** (LM Studio/Ollama/llama.cpp).
Those desktop runtimes do not run on Android, so packaging this exact app
for Android (Option D, Kivy/BeeWare) is **not viable** — there would be
nothing to benchmark on-device, and PySide6 has no supported Android target.

Recommended path:

1. **Option B now (zero code):** the community website in `web/` is
   responsive; the benchmark app/server run on a desktop while a phone
   browses, controls, and compares results over the LAN. This already works.
2. **Option C next (small app):** a thin viewer/uploader app (Flutter or
   Kotlin) talking to the same `/api/*` endpoints — browse, compare, and
   submit results captured on desktops.
3. **Option A only if on-device benchmarking becomes a goal:** a separate
   Android benchmark backend (llama.cpp compiled for Android/NNAPI/Vulkan,
   e.g. via MLC or llama.cpp Android builds) with its own engine — a new
   project, sharing only the result schema and upload API.

The result schema already carries `platform.os` and `platform.arch`, so
Android-sourced results can join the same database without changes.
