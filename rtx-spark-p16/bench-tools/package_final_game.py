"""Copy the chosen NEON SPARK version into coding/neon-spark-final with the prompt chain that made it.

Usage: package_final_game.py <version folder under neon-spark-iterated, e.g. v9>

Writes index.html (the game, unchanged), stats.json (that round's generation stats) and
prompts.txt: the one-shot prompt and every follow-up prompt in order, each with its round's
token counts, minutes and speed, all from the local Qwen3.8-27B.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rtx_spark_bench as rb  # noqa: E402

CODING = rb.OUT / "coding"


def stats_line(folder: Path) -> str:
    s = json.loads((folder / "stats.json").read_text(encoding="utf-8"))
    u = s.get("usage") or {}
    return (f"{u.get('prompt_tokens')} tokens in, {u.get('completion_tokens')} tokens out, "
            f"{s['total_s'] / 60:.1f} minutes, {s.get('decode_tps'):.1f} tok/s, {s.get('html_lines')} lines of HTML")


def main() -> int:
    chosen = sys.argv[1]
    versions = sorted((p for p in (CODING / "neon-spark-iterated").glob("v*") if p.is_dir()), key=lambda p: int(p.name[1:]))
    versions = [p for p in versions if int(p.name[1:]) <= int(chosen[1:])]
    out = CODING / "neon-spark-final"
    out.mkdir(exist_ok=True)
    shutil.copy2(CODING / "neon-spark-iterated" / chosen / "index.html", out / "index.html")
    shutil.copy2(CODING / "neon-spark-iterated" / chosen / "stats.json", out / "stats.json")

    one_shot = CODING / "neon-spark"
    parts = ["NEON SPARK: every prompt sent to Qwen3.8-27B (UD-Q4_K_M, DFlash2 draft, medium reasoning) on the RTX Spark laptop.",
             "Each follow-up was sent with the original prompt and the previous version's full code; no line of the game was edited by hand.",
             "",
             f"=== Prompt 1 (one-shot) - {stats_line(one_shot)} ===",
             (one_shot / "prompt.txt").read_text(encoding="utf-8").strip()]
    for i, v in enumerate(versions, start=2):
        parts += ["", f"=== Prompt {i} ({v.name}) - {stats_line(v)} ===", (v / "feedback.txt").read_text(encoding="utf-8").strip()]
    (out / "prompts.txt").write_text("\n".join(parts) + "\n", encoding="utf-8-sig")  # BOM: browsers open it as UTF-8
    (out / "version.txt").write_text(chosen + "\n", encoding="utf-8")  # export_csv.py stops the iteration table here
    print(f"final = {chosen}: {out / 'index.html'}, {len(versions) + 1} prompts in {out / 'prompts.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
