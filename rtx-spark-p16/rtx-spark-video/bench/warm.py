"""Lab 2 and Lab 3 with every model already loaded, as in a live session: each runs twice, the second is kept.
Writes bench/bench_warm.json (the same event format as run_bench.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import run_bench as rb  # noqa: E402

Q2 = "How long after opening the DC disconnect must I wait before removing a module cover?"
Q3 = "Analyse sales by region and tell me which region grew the most."
out = {}
for _ in range(2):
    out['lab2_plain'] = rb.stream(f"{rb.APP}/api/plain/stream", {"question": Q2, "lang": "en"})
    out['lab2_rag'] = rb.stream(f"{rb.APP}/api/lab2/ask/stream", {"question": Q2, "lang": "en", "k": 5})
    out['lab3'] = rb.stream(f"{rb.APP}/api/lab3/run", {"question": Q3, "lang": "en", "route": "auto"})
    print({k: v[-1]['total_s'] for k, v in out.items()}, flush=True)
(Path(__file__).parent / 'bench_warm.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
