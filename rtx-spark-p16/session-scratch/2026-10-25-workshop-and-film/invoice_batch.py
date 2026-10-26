"""Restart the batch engine with given llama-server flags, then time N invoices sent concurrently.

    python invoice_batch.py <app dir> "<extra llama-server args>" <count> <concurrency>
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, sys.argv[1])
os.environ["BATCH_LLAMA_ARGS"] = sys.argv[2]
import enterprise as ent  # noqa: E402  (reads BATCH_LLAMA_ARGS when it starts the engine)

count, conc = int(sys.argv[3]), int(sys.argv[4])
DEMO = sys.argv[5] if len(sys.argv) > 5 else "invoices"
ent.engine_stop()
time.sleep(3)
t0 = time.time()
ok, why = ent.engine_start()
if not ok or not ent.engine_wait(timeout=600):
    print("engine failed:", why, ent.engine_log_tail(30))
    raise SystemExit(1)
print(f"args {sys.argv[2]!r}: engine ready in {time.time() - t0:.0f}s", flush=True)

rows = ent.items(DEMO)[300:300 + count]  # not the ones processed before (no prompt cache help)


def one(it):
    t = time.time()
    res = ent.PROCESS[DEMO]("vllm", it)
    sc = (ent.score_invoice(res, it) if DEMO == "invoices" else ent.score_inbox(res, it["truth"]))
    return sum(sc.values()), time.time() - t


t0 = time.time()
with ThreadPoolExecutor(conc) as pool:
    results = list(pool.map(one, rows))
wall = time.time() - t0
right = sum(r for r, _ in results)
print(f"  {count} {DEMO} at concurrency {conc}: {wall:.0f}s wall, {60 * count / wall:.1f}/min, "
      f"{right} fields right, slowest request {max(s for _, s in results):.0f}s", flush=True)
evals = [l for l in ent.engine_log_tail(2000).splitlines() if "prompt eval time" in l and "tokens (" in l]
big = [l.split("prompt eval time =")[1].strip() for l in evals if "/  2" in l or "/ 2" in l][:3]
print("  sample prompt evals:", big)
