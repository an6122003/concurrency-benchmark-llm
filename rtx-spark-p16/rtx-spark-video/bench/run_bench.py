"""Benchmarks for the RTX Spark video, measured on this laptop through the installed workshop.

Records model speeds (Ollama), each lab run end to end through the app's own API (Lab 1 training
with its loss curve, the Lab 1 comparison, Lab 2 with and without RAG, Lab 3's agent), three short
Enterprise batches, and the GPU's load, power, temperature and memory every half second throughout.
Writes bench/bench.json. Leaves the Enterprise jobs reset afterwards.

    python run_bench.py [--skip-ent]
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

APP = "http://127.0.0.1:8090"
OLLAMA = "http://127.0.0.1:11434"
HERE = Path(__file__).resolve().parent
CORPUS = Path.home() / "ai-workshop" / "hands-on-2-rag" / "corpus"
T0 = time.time()
OUT: dict = {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "phases": [], "gpu": []}


def now() -> float:
    return round(time.time() - T0, 3)


def log(msg: str) -> None:
    print(f"[{now():7.1f}s] {msg}", flush=True)


def post(url: str, body: dict, timeout: float = 600) -> dict:
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get(url: str, timeout: float = 60) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


def stream(url: str, body: dict | None = None, timeout: float = 900) -> list[dict]:
    """POST (or GET) an NDJSON stream; keep every event with its time, text deltas only counted."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, {"Content-Type": "application/json"} if data else {})
    events, deltas, first_delta, t = [], 0, None, time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for line in r:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            dt = round(time.time() - t, 3)
            if ev.get("event") == "delta":
                deltas += 1
                if first_delta is None:
                    first_delta = dt
                continue
            ev["_t"] = dt
            events.append(ev)
    return events + [{"event": "_stream", "deltas": deltas, "first_delta_s": first_delta, "total_s": round(time.time() - t, 3)}]


class Phase:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.start = now()
        log(f"--> {self.name}")
        return self

    def __exit__(self, *exc):
        OUT["phases"].append({"name": self.name, "start": self.start, "end": now()})
        log(f"<-- {self.name} ({now() - self.start:.1f}s)")
        save()  # after every phase: a later failure keeps what was measured


OUTFILE = HERE / ("bench_labs.json" if "--skip-ent" in sys.argv else "bench.json")


def save() -> None:
    OUTFILE.write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")


def gpu_sampler(stop: threading.Event) -> None:
    q = "utilization.gpu,power.draw,temperature.gpu,memory.used,clocks.sm"
    p = subprocess.Popen(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits", "-lms", "500"],
                         stdout=subprocess.PIPE, text=True)
    for line in p.stdout:
        if stop.is_set():
            break
        parts = [x.strip() for x in line.split(",")]
        if len(parts) < 5 or not parts[0].replace(".", "", 1).isdigit():
            continue  # the NPU row, or a header
        def f(x):
            try:
                return float(x)
            except ValueError:
                return None
        OUT["gpu"].append({"t": now(), "util": f(parts[0]), "power_w": f(parts[1]), "temp_c": f(parts[2]),
                           "mem_mb": f(parts[3]), "sm_mhz": f(parts[4])})
    p.terminate()


def ollama_gen(model: str, prompt: str, n: int, think: bool | None = None) -> dict:
    body = {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": n, "temperature": 0, "seed": 7}}
    if think is not None:
        body["think"] = think
    r = post(f"{OLLAMA}/api/generate", body)
    ns = 1e9
    return {"model": model, "prompt_tokens": r.get("prompt_eval_count"), "gen_tokens": r.get("eval_count"),
            "prompt_tps": round(r["prompt_eval_count"] / (r["prompt_eval_duration"] / ns), 1) if r.get("prompt_eval_duration") else None,
            "gen_tps": round(r["eval_count"] / (r["eval_duration"] / ns), 1) if r.get("eval_duration") else None,
            "load_s": round(r.get("load_duration", 0) / ns, 2), "total_s": round(r.get("total_duration", 0) / ns, 2)}


def main() -> int:
    skip_ent = "--skip-ent" in sys.argv
    stop = threading.Event()
    threading.Thread(target=gpu_sampler, args=(stop,), daemon=True).start()
    time.sleep(2)

    passages = [p.read_text(encoding="utf-8")[:1500] for p in sorted(CORPUS.glob("*.md"))[:32]]
    long_prompt = ("Summarise the key safety rules in these manuals.\n\n" + "\n\n".join(passages[:6]))[:9000]
    short_prompt = "Explain step by step how a grid-scale battery energy storage system charges, stores and discharges energy."

    with Phase("idle"):
        time.sleep(6)

    with Phase("ollama"):
        res = []
        for model, think in (("nemotron-3.5-lightning:30b-a3b", False), ("qwen2.5:1.5b-instruct", None),
                             ("aurora-assistant", None)):
            ollama_gen(model, "Hi", 8, think)  # load + warm up
            for _ in range(2):
                res.append({"kind": "short", **ollama_gen(model, short_prompt, 256, think)})
            res.append({"kind": "long_prompt", **ollama_gen(model, long_prompt, 64, think)})
            log(f"{model}: {res[-2]['gen_tps']} tok/s generate, {res[-1]['prompt_tps']} tok/s prompt")
        emb = []
        post(f"{OLLAMA}/api/embed", {"model": "qwen3-embedding:4b", "input": passages[:2]})
        for _ in range(3):
            t = time.time()
            post(f"{OLLAMA}/api/embed", {"model": "qwen3-embedding:4b", "input": passages})
            emb.append(round(len(passages) / (time.time() - t), 2))
        OUT["ollama"] = {"runs": res, "embed_passages_per_s": emb, "embed_batch": len(passages)}
        OUT["ollama_ps"] = get(f"{OLLAMA}/api/ps")

    with Phase("lab1_train"):
        info = get(f"{APP}/api/lab1/info")
        start = post(f"{APP}/api/lab1/train", {"epochs": 5, "lr": 2e-4, "rank": 16})
        OUT["lab1_train"] = {"start": start, "events": stream(f"{APP}/api/lab1/stream?from=0"),
                             "info_before": info.get("last_run"), "info_after": get(f"{APP}/api/lab1/info").get("last_run")}

    with Phase("lab1_compare"):
        OUT["lab1_compare"] = stream(f"{APP}/api/lab1/compare", {"question": "Who built you, and what are you for?"})

    q2 = "How long after opening the DC disconnect must I wait before removing a module cover?"
    with Phase("lab2_plain"):
        OUT["lab2_plain"] = stream(f"{APP}/api/plain/stream", {"question": q2, "lang": "en"})
    with Phase("lab2_rag"):
        OUT["lab2_rag"] = stream(f"{APP}/api/lab2/ask/stream", {"question": q2, "lang": "en", "k": 5})

    q3 = "Analyse sales by region and tell me which region grew the most."
    with Phase("lab3_agent"):
        OUT["lab3"] = stream(f"{APP}/api/lab3/run", {"question": q3, "lang": "en", "route": "auto"})

    if not skip_ent:
        OUT["ent"] = {}
        try:
            for demo, limit in (("inbox", 300), ("invoices", 40), ("calls", 20)):
                with Phase(f"ent_{demo}"):
                    post(f"{APP}/api/ent/reset", {"demo": demo})
                    started = post(f"{APP}/api/ent/start", {"demo": demo, "limit": limit, "engine": "vllm"})
                    polls, deadline = [], time.time() + 1200
                    while time.time() < deadline:
                        time.sleep(2)
                        s = get(f"{APP}/api/ent/summary")["demos"][demo]
                        run = s.get("run") or {}
                        polls.append({"t": now(), "processed": s.get("processed"), "status": s.get("status"),
                                      "done": run.get("done"), "rate": s.get("rate_per_min"), "power_w": s.get("power_w")})
                        if run.get("ended"):  # the batch is over (finished, stopped or failed)
                            break
                    OUT["ent"][demo] = {"limit": limit, "started": started, "polls": polls, "final": s}
                    log(f"{demo}: {s.get('processed')} done, {s.get('rate_per_min')}/min, accuracy {s.get('accuracy')}")
        finally:
            for demo in ("inbox", "invoices", "calls"):
                try:
                    post(f"{APP}/api/ent/stop", {"demo": demo})
                except Exception:
                    pass
            time.sleep(5)
            for demo in ("inbox", "invoices", "calls"):
                try:
                    post(f"{APP}/api/ent/reset", {"demo": demo})
                except Exception as exc:
                    log(f"reset {demo}: {exc}")

    with Phase("cooldown"):
        time.sleep(8)
    stop.set()
    OUT["telemetry"] = get(f"{APP}/api/telemetry")
    save()
    log(f"wrote {OUTFILE} ({len(OUT['gpu'])} GPU samples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
