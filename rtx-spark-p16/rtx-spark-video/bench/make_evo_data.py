"""The evolution cut's numbers: each NEON SPARK prompt's lines of HTML, minutes and speed, from the report's
iteration table (export_csv.py), plus the cut of the score it plays on. Writes comp/evo-data.js.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITER = Path(r"C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\report-data\iteration.csv")

rows = list(csv.DictReader(ITER.open(encoding="utf-8")))
rounds = [{"n": i + 1, "folder": r["folder"], "lines": int(r["html_lines"]), "minutes": float(r["total_min"]),
           "tps": float(r["decode_tps"])} for i, r in enumerate(rows)]
data = json.loads((ROOT / "comp" / "data.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
q = data["quick"]
# The score: the quick cut's own downbeats, from the bar before the drop for five bars (track 5.87-15.87), then
# straight into its peak for four (track 63.75-71.75), joined on the downbeat. 18 s in all.
seg1 = [q["segments"][0][0], round(q["segments"][0][0] + q["downbeats"][5], 3)]
peak = q["segments"][1][0] + (q["downbeats"][13] - q["downbeats"][12])
seg2 = [round(peak, 3), round(peak + 8.0, 3)]
cut_bars = q["downbeats"][:6] + [round(q["downbeats"][5] + 2.0 * k, 3) for k in range(1, 5)]
evo = {"rounds": rounds, "total_minutes": round(sum(r["minutes"] for r in rounds), 1),
       "final_lines": rounds[-1]["lines"], "first_lines": rounds[0]["lines"],
       "score": {"take": q["take"], "segments": [seg1, seg2]}, "downbeats": cut_bars,
       "end": round(seg1[1] - seg1[0] + seg2[1] - seg2[0], 3)}
(ROOT / "comp" / "evo-data.js").write_text("window.EVO = " + json.dumps(evo, indent=1) + ";\n", encoding="utf-8")
print(json.dumps({k: v for k, v in evo.items() if k != "rounds"}), [(r["n"], r["lines"], r["minutes"]) for r in rounds])
