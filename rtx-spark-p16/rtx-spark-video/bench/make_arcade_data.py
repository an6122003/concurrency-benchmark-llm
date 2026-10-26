"""The arcade cut's numbers: what each NEON SPARK prompt cost the local model (tokens in and out, the context it
filled, minutes, speed, lines of HTML) and the totals, from the report's iteration table and each round's server
arguments (its context window). Writes comp/arcade-data.js.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = Path(r"C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025")
CODING = RUNS / "coding"


def window(folder: str) -> int:
    path = CODING / ("neon-spark" if folder == "neon-spark" else f"neon-spark-iterated/{folder}") / "server-args.json"
    args = json.loads(path.read_text(encoding="utf-8"))
    return int(args[args.index("-c") + 1])


rows = list(csv.DictReader((RUNS / "report-data" / "iteration.csv").open(encoding="utf-8")))
rounds = []
for i, r in enumerate(rows):
    pin, pout = int(r["prompt_tokens"]), int(r["completion_tokens"])
    rounds.append({"n": i + 1, "folder": r["folder"], "tokens_in": pin, "tokens_out": pout, "context": pin + pout,
                   "window": window(r["folder"]), "minutes": float(r["total_min"]), "tps": float(r["decode_tps"]),
                   "lines": int(r["html_lines"])})
peak = max(rounds, key=lambda r: r["context"])
stats = json.loads((CODING / "neon-spark-final" / "stats.json").read_text(encoding="utf-8"))
minutes = sum(r["minutes"] for r in rounds)
out = sum(r["tokens_out"] for r in rounds)
data = {
    "rounds": rounds,
    "totals": {"prompts": len(rounds), "tokens_out": out, "tokens_in": sum(r["tokens_in"] for r in rounds),
               "minutes": round(minutes, 1), "tps": round(out / (minutes * 60), 1), "lines": rounds[-1]["lines"],
               "peak_context": peak["context"], "peak_window": peak["window"], "peak_prompt": peak["n"]},
    "model": {"name": stats["model"], "quant": stats["quant"].replace("UD-", ""), "draft": "DFlash2",
              "effort": stats["effort"], "hardware": "RTX Spark laptop"},
}
(ROOT / "comp" / "arcade-data.js").write_text("window.ARC = " + json.dumps(data, indent=1) + ";\n", encoding="utf-8")
print(json.dumps(data["totals"]), json.dumps(data["model"]))
