# RTX Spark P16: the benchmark and everything made from it

A benchmark of the ASUS ProArt P16 (NVIDIA RTX Spark N1X, 128 GB unified memory, Windows 11 on Arm), run on
2026-10-25/26 with this repository's suite, plus the report, the games and the films made from it. These files were
moved off the demo laptop before it went back; on that laptop they lived in `C:\Users\ProArt\Desktop\Project\`.

| Folder | What is in it |
|---|---|
| [`../suite-results-rtx-spark-p16-20261025/`](../suite-results-rtx-spark-p16-20261025/) | The raw results: one folder per model, the speculative-decoding showdown (`spec-showdown/`), the VRAM-setting evidence (`evidence/`) and `dataset.json`. `coding/` holds the coding test: the NEON SPARK one-shot, its ten prompt iterations (prompts, model streams, screenshots) and the final game (`neon-spark-final/index.html`). |
| [`rtx-spark-report/`](rtx-spark-report/) | The final report. Open `index.html` in a browser: charts, infographics, conclusions and the playable games. It works offline. |
| [`bench-tools/`](bench-tools/) | The pipeline and benchmark scripts, the report's sources and builders (`report/`, rebuilt with `build_local_report.py --suite --game`), the coding prompts and the run logs. |
| [`rtx-spark-video/`](rtx-spark-video/) | The films and their sources. See the list below. |

The finished films in `rtx-spark-video/out/`:

- `rtx-spark-film-16x9.mp4` and `rtx-spark-film-9x16.mp4`: the 72 s film, with `-share` encodes under 30 MB.
- `rtx-spark-quicktest-9x16.mp4`: the 38 s TikTok quick test.
- `neon-spark-evolution-9x16.mp4`: the game, prompt by prompt (18 s).
- `neon-spark-arcade-9x16.mp4`: the game-styled cut with the build stats (19 s).

The sources to re-render them are also in `rtx-spark-video/`: the pages in `comp/` with their captured gameplay clips, `audio/` and `bench/`.

## Not included

These can be rebuilt or downloaded again:

- **`rtx-spark-video/out/frames-*`**: 1.9 GB of rendered frames. Re-render them from `comp/` with `bench/render_frames.py` (or `render.ps1`).
- **`rtx-spark-video/out/edge-*`**: headless Edge profiles.
- **`bench-tools/llamacpp-cuda-b11671/`**: llama.cpp b11671 (ba3c05f71), the CUDA 13 win32-arm64 build copied from Hermes Agent. Two of its DLLs are over GitHub's 100 MB file limit.
- **The models and tools**: `~\models`, the Ollama and Hugging Face caches, ffmpeg and Python.

The scripts use absolute paths under `C:\Users\ProArt\Desktop\Project\`. Change them before rebuilding anything on another machine.
