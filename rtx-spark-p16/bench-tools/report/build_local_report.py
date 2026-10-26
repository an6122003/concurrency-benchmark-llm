"""Build the RTX Spark report as a folder of local HTML files that open offline.

Usage: build_local_report.py [--suite] [--game] [--out DIR]

Same page and charts as the dashboard version (index.html, charts.js), with the benchmark
tables embedded as JSON, mini-d3.js and dash-local.js standing in for the dashboard runtime,
full-size screenshots, the generated games and their replays, and the CSV files themselves.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import build_report as br

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = Path(r"C:\Users\ProArt\Desktop\Project\rtx-spark-report")

# (file in games/, source under coding/, flag or None, what it is)
GAMES = [
    ("neon-spark-one-shot.html", "neon-spark/index.html", None, "NEON SPARK from one prompt, untouched"),
    ("neon-spark-one-shot-replay.html", "neon-spark/replay.html", None, "Replay of that one-shot generation with its real timing"),
    ("galaxy-forge.html", "galaxy-forge/index.html", None, "Galaxy Forge from one prompt, untouched"),
    ("galaxy-forge-replay.html", "galaxy-forge/replay.html", None, "Replay of the Galaxy Forge generation"),
    ("neon-spark-final.html", "neon-spark-final/index.html", "game", "NEON SPARK after the follow-up prompts: the final version"),
    ("neon-spark-prompts.txt", "neon-spark-final/prompts.txt", "game", "Every prompt that made the final NEON SPARK, in order, with each round's stats"),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RTX Spark LLM Benchmark</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap">
<style>
  /* Light ProArt studio surface: porcelain page, white cards, graphite type; NVIDIA green marks the laptop. */
  :root {
    --font-anthropic-sans: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
    --font-anthropic-serif: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
    --color-bg: #f5f4f1; --color-fg: #24262b; --color-fg-muted: #6b6d74; --color-panel: #ffffff;
    --color-border-line: #e3e0d8; --color-ok: #3d7a00; --color-warn: #a8660b; --color-bad: #b3261e;
    --cds-font-size-caption: 12.5px; --cds-font-size-body: 15px; --cds-font-size-heading: 19px; --cds-font-size-title: 34px;
    --cds-font-weight-medium: 600;
    --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 16px; --cds-gap-lg: 24px; --cds-gap-xl: 44px;
    --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 20px; --cds-pad-xl: 32px;
    --cds-radius: 12px;
    --cds-chart-grid: #eeebe4; --cds-chart-axis: #cbc7bd; --cds-chart-reference: #8f9199; --cds-chart-muted: #bdb9b0;
    --cds-surface-popover: #ffffff; --cds-border: #e3e0d8; --cds-shadow-popover: 0 8px 28px rgba(36, 38, 43, .14);
    --cds-text-secondary: #6b6d74; --cds-dur-slow: 420ms; --cds-ease-out: cubic-bezier(.2, .8, .2, 1);
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); }
  #dash-root { max-width: 1240px; margin: 0 auto; padding: 44px 32px 64px; }
  #dash-root::before { content: ""; display: block; height: 3px; border-radius: 2px; margin-bottom: 28px;
    background: linear-gradient(90deg, #b8925a, #e6cf9f 45%, #76b900); }
  .rs-title { font-weight: 300; letter-spacing: -0.01em; }
  .rs-tile .v { font-weight: 300; }
  .dash-skeleton { }
  @media (max-width: 640px) { #dash-root { padding: 24px 16px 48px; } }
</style>
</head>
<body>
<script id="rs-data" type="application/json">__DATA__</script>
<script src="lib/mini-d3.js"></script>
<script src="lib/dash-local.js"></script>
<div id="dash-root">
__PAGE__
</div>
</body>
</html>
"""


def thumb(src: Path, dst: Path, width: int = 1280, quality: int = 82) -> None:
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "thumb.ps1"),
                    str(src), str(dst), str(width), str(quality)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", action="store_true", help="the concurrency suite has finished")
    ap.add_argument("--game", action="store_true", help="the iterated game is final")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    flags = {f for f in ("suite", "game") if getattr(args, f)} | {"local"}
    out = Path(args.out)
    for sub in ("lib", "data", "shots", "games"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    tables, file_rows = {}, []
    for id_, (name, flag, title, desc) in br.DATASETS.items():
        src = br.DATA / name
        if (flag and flag not in flags) or not src.exists():
            continue
        with src.open(encoding="utf-8", newline="") as f:
            tables[id_] = list(csv.DictReader(f))
        shutil.copy2(src, out / "data" / name)
        file_rows.append((f"data/{name}", f"{title}. {desc}"))
    for name, source, flag, what in GAMES:
        src = br.CODING / source
        if (flag and flag not in flags) or not src.exists():
            continue
        shutil.copy2(src, out / "games" / name)
        file_rows.append((f"games/{name}", what))

    shots = []
    for image, flag, alt, caption in br.SHOTS:
        if flag and flag not in flags:
            continue
        name = image.replace("/shots/", "-").replace("/", "-")
        thumb(br.CODING / image, out / "shots" / name)
        shots.append({"src": f"shots/{name}", "alt": alt, "caption": caption})
    (out / "lib" / "shots.js").write_text(
        "// Screenshots of the apps Qwen3.8-27B wrote (built by build_local_report.py).\n"
        f"window.RS_SHOTS = {json.dumps(shots, indent=1)};\n", encoding="utf-8")
    for lib in ("mini-d3.js", "dash-local.js"):
        shutil.copy2(HERE / "local" / lib, out / "lib" / lib)
    # The dashboard runs each script in its own scope; a plain page shares one, so each gets a function scope.
    scoped = lambda code: f"(() => {{\n{code.strip()}\n}})();\n"  # noqa: E731
    (out / "lib" / "charts.js").write_text(scoped((HERE / "charts.js").read_text(encoding="utf-8")), encoding="utf-8")

    page = br.keep_blocks((HERE / "index.html").read_text(encoding="utf-8"), flags)
    page = re.sub(r"<script>(.*?)</script>", lambda m: f"<script>{scoped(m.group(1))}</script>", page, flags=re.S)
    page = page.replace('<script src="shots.js"></script>', '<script src="lib/shots.js"></script>')
    page = page.replace('<script src="charts.js"></script>', '<script src="lib/charts.js"></script>')
    rows = "".join(f'<tr><td><a href="{html.escape(p)}">{html.escape(p)}</a></td><td class="txt">{html.escape(t)}</td></tr>'
                   for p, t in file_rows)
    page = page.replace("<!--local:files-->", rows)
    named = {t for attr in re.findall(r'data-source="([^"]+)"', page) for t in attr.split()}
    calcs = set(re.findall(r"dash\.calc\('([\w-]+)'", page))
    missing = named - set(tables) - calcs
    if missing:
        raise SystemExit(f"the page names sources that have no table: {sorted(missing)}")
    data = json.dumps(tables, ensure_ascii=False).replace("</", "<\\/")
    (out / "index.html").write_text(PAGE.replace("__DATA__", data).replace("__PAGE__", page), encoding="utf-8")
    print(f"wrote {out / 'index.html'}: flags {sorted(flags)}, tables {sorted(tables)}, {len(shots)} screenshots, "
          f"{sum(1 for p, _ in file_rows if p.startswith('games/'))} game files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
