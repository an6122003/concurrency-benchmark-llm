"""Build the store documents for the RTX Spark report dashboard.

Usage: build_report.py [--suite] [--game] --out DIR

Keeps or drops the page's <!--only:X--> / <!--unless:X--> blocks (X is suite or game),
makes shots.js from the screenshot list (resized by thumb.ps1), and writes one JSON file per
store document: dash/meta, datasets/<id> (sources from assets.json, the uploaded CSV urls)
and files/<name>. Prints the batch entries for the dashboard's store.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rtx_spark_bench as rb  # noqa: E402

DATA = rb.OUT / "report-data"
CODING = rb.OUT / "coding"
BY = "Claude, from benchmark runs on the RTX Spark laptop"
LOCAL = "Measured locally on the ASUS ProArt P16 (RTX Spark N1X, 128 GB)."

# id: (file, flag or None, title, description)
DATASETS = {
    "models": ("models.csv", None, "Models tested",
               "One row per model: design, parameter counts, quantization and file size of the GGUF on the laptop."),
    "bench": ("llama_bench.csv", None, "llama-bench speed runs",
              "llama-bench pp512 and tg128 (five runs each), and pp2048 and tg32 at 0 to 32,768 tokens of context (three runs each)."),
    "spec": ("spec.csv", None, "Speculative decoding runs",
             "Qwen3.8-27B through llama-server without speculation, with MTP (2 and 3 draft tokens) and with the DFlash2 draft model, three 768-token prompts each."),
    "coding": ("coding.csv", None, "One-shot coding runs",
               "Qwen3.8-27B with DFlash2 and medium reasoning effort: one prompt per app, timed from request to last token."),
    "iteration": ("iteration.csv", "game", "Game iteration prompts",
                  "NEON SPARK from the one-shot prompt through each follow-up prompt to the same local Qwen3.8-27B."),
    "vram": ("vram_ab.csv", None, "GPU memory setting runs",
             "llama-bench runs of the two largest models at the 50 GB and 96 GB GPU memory settings, with peak memory from Windows performance counters."),
    "shared": ("shared_test.csv", None, "Shared memory test",
               "The same llama-bench run with the weights in dedicated GPU memory, then forced into shared memory, then dedicated again."),
    "dgx": ("reference.csv", None, "DGX Spark comparison",
            "gpt-oss-20b llama-bench on the laptop beside the DGX Spark figures from llama.cpp's published benchmark table for the same command."),
    "battery": ("battery.csv", None, "Battery vs charger runs",
                "Qwen3.6-35B-A3B llama-bench on battery only and on the 65 W charger, minutes apart."),
    "power": ("power.csv", None, "GPU power telemetry",
              "nvidia-smi samples once a second during each model's runs, averaged over the samples with the GPU busy."),
    "facts": ("facts.csv", None, "Setup measurements",
              "Memory figures read from the laptop's own logs: the GPU memory CUDA reports, and the size of Qwen3.8-Flash-Next's embedding table."),
    "phases": ("phases.csv", None, "Benchmark phase log",
               "Every finished GPU phase from the run manifest: model, charger, start time, minutes, and the battery level at its start and end."),
    "conc": ("concurrency.csv", "suite", "Concurrency suite results",
             "concurrency-benchmark-llm summaries per model, scenario and number of people at once, through llama-server's OpenAI API."),
    "batched": ("batched.csv", "suite", "Batched decode ceiling",
                "llama-batched-bench with 512-token prompts and 128 generated tokens for 1 to 32 parallel sequences."),
    "context": ("context.csv", "suite", "Long-document requests",
                "One-person requests from the suite's 4K, 8K and 16K-word document scenarios: prompt size and time to first token."),
}

# (image, flag or None, alt, caption)
SHOTS = [
    ("neon-spark/shots/01-title.jpg", None, "NEON SPARK title screen", "NEON SPARK from one prompt: the title screen"),
    ("neon-spark/shots/04-play.jpg", None, "NEON SPARK gameplay with a boss ship",
     "NEON SPARK from one prompt: it skipped straight to the boss wave"),
    ("galaxy-forge/shots/05-neon.jpg", None, "Galaxy Forge spiral galaxy with its control panel",
     "Galaxy Forge from one prompt: an interactive galaxy with live controls"),
    ("neon-spark-iterated/v10/shots/03-intro-4s.jpg", "game", "NEON SPARK intro transmission",
     "Final NEON SPARK: the story arrives as an incoming transmission"),
    ("neon-spark-iterated/v10/shots/16-s2-wave.jpg", "game", "NEON SPARK sector 2 with armored enemies",
     "Final: every sector has its own palette and enemy mix"),
    ("neon-spark-iterated/v10/shots-bossdeath/c-death-0.7s.jpg", "game", "A NEON SPARK boss breaking apart",
     "Final: bosses break apart and say a last line"),
    ("neon-spark-iterated/v10/shots/14-upgrade-cards.jpg", "game", "NEON SPARK upgrade cards",
     "Final: pick one of three upgrades after each boss"),
    ("neon-spark-iterated/v10/shots/27-final-boss-fight.jpg", "game", "NEON SPARK final boss, The Static",
     "Final: the last boss, The Static, with the full HUD"),
    ("neon-spark-iterated/v10/shots/30-victory.jpg", "game", "NEON SPARK victory screen",
     "Final: the ending, stats and Hard mode"),
]


def keep_blocks(text: str, flags: set[str]) -> str:
    def only(m):
        return m.group(2) if m.group(1) in flags else ""

    def unless(m):
        return "" if m.group(1) in flags else m.group(2)

    while True:  # blocks can nest: each pass resolves the outermost ones
        before = text
        text = re.sub(r"<!--only:(\w+)-->(.*?)<!--/only:\1-->", only, text, flags=re.S)
        text = re.sub(r"<!--unless:(\w+)-->(.*?)<!--/unless:\1-->", unless, text, flags=re.S)
        if text == before:
            break
    left = re.findall(r"<!--/?(?:only|unless):\w+-->", text)
    if left:
        raise SystemExit(f"unmatched block markers: {left}")
    return text


def shots_js(flags: set[str], work: Path) -> str:
    items = []
    for image, flag, alt, caption in SHOTS:
        if flag and flag not in flags:
            continue
        src = CODING / image
        dst = work / ("thumb-" + image.replace("/", "-"))
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "thumb.ps1"), str(src), str(dst)],
                       check=True)
        data = base64.b64encode(dst.read_bytes()).decode("ascii")
        items.append({"src": f"data:image/jpeg;base64,{data}", "alt": alt, "caption": caption})
    return "// Screenshots of the apps Qwen3.8-27B wrote, as data URLs (built by build_report.py).\n" \
           f"window.RS_SHOTS = {json.dumps(items, indent=1)};\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", action="store_true", help="the concurrency suite has finished")
    ap.add_argument("--game", action="store_true", help="the iterated game is final")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    flags = {f for f in ("suite", "game") if getattr(args, f)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assets = json.loads((HERE / "assets.json").read_text(encoding="utf-8"))

    page = keep_blocks((HERE / "index.html").read_text(encoding="utf-8"), flags)
    charts = (HERE / "charts.js").read_text(encoding="utf-8")
    shots = shots_js(flags, out)
    docs = [("dash", "meta", {"title": "RTX Spark LLM Benchmark"})]
    used = set()
    for id_, (name, flag, title, desc) in DATASETS.items():
        if flag and flag not in flags:
            continue
        if name not in assets:
            raise SystemExit(f"{name} is not uploaded yet (add its url to assets.json)")
        at = datetime.fromtimestamp((DATA / name).stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
        docs.append(("datasets", id_, {"title": title, "description": f"{desc} {LOCAL}",
                                        "source": {"kind": "file", "url": assets[name], "name": name},
                                        "updated": {"at": at, "by": BY}, "fixed": True}))
        used.add(id_)
    docs += [("files", "index.html", {"text": page}), ("files", "charts.js", {"text": charts}), ("files", "shots.js", {"text": shots})]

    calcs = set(re.findall(r"dash\.calc\('([\w-]+)'", page))
    named = {t for attr in re.findall(r'data-source="([^"]+)"', page) for t in attr.split()}
    unknown = named - used - calcs
    if unknown:
        raise SystemExit(f"the page names sources that are not defined: {sorted(unknown)}")

    batch, total = [], 0
    for collection, doc_id, body in docs:
        path = out / f"{collection}__{doc_id}.json"
        text = json.dumps(body, ensure_ascii=False)
        if len(text.encode("utf-8")) > 256 * 1024:
            raise SystemExit(f"{collection}/{doc_id} is over 256 KB")
        path.write_text(text, encoding="utf-8")
        total += len(text.encode("utf-8"))
        batch.append({"op": "set", "collection": collection, "doc_id": doc_id, "file_path": str(path)})
    print(f"flags {sorted(flags) or 'none'}: {len(batch)} documents, {total / 1024:.0f} KB; datasets {sorted(used)}; calcs {sorted(calcs)}")
    (out / "batch.json").write_text(json.dumps(batch, indent=1), encoding="utf-8")
    print(json.dumps(batch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
