"""Time single invoice requests on an idle batch engine (one at a time)."""
import sys
import time

sys.path.insert(0, sys.argv[1])  # the workshop's app folder
import enterprise as ent  # noqa: E402

if not ent.engine_ready():
    ok, why = ent.engine_start()
    print("engine start:", ok, why, flush=True)
    if not ent.engine_wait(timeout=600):
        print(ent.engine_log_tail(30))
        raise SystemExit(1)
rows = ent.items("invoices")[:3]
for it in rows:
    t0 = time.time()
    res = ent.process_invoice("vllm", it)
    sc = ent.score_invoice(res, it)
    print(f"{it['id']}: {time.time() - t0:.1f}s, tokens in {res['tokens_in']} out {res['tokens_out']}, "
          f"{sum(sc.values())}/{len(sc)} right", flush=True)
print("\n".join(l for l in ent.engine_log_tail(400).splitlines() if "prompt eval time" in l or "image" in l.lower())[-3000:])
