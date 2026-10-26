"""Collect every benchmark output into one dataset.json for the report.

Reads, per model folder under suite-results-rtx-spark-p16-20261025:
  bench-classic.json / bench-sweep.json   llama-bench
  batched.jsonl / batched-ref.jsonl       llama-batched-bench
  suite/<key>/<scenario>/results.json     concurrency-benchmark-llm suite
  suite-mtp/<key>/<scenario>/results.json the same scenarios with MTP
  server-*.log                            per-request server timings and memory buffers
  telemetry-*-gpu.csv / -gpumem.csv       GPU power, clocks, temperature, memory
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rtx_spark_bench as rb  # noqa: E402

TIMING = re.compile(r"task\s+(\d+) \|\s+(prompt eval|eval) time =\s+([\d.]+) ms /\s+(\d+) tokens")
DRAFT = re.compile(r"task\s+(\d+) \| draft acceptance = ([\d.]+) \(\s*(\d+) accepted /\s*(\d+) generated\), mean len =\s*([\d.]+)")
BUFFER = re.compile(r"(CUDA0|CUDA_Host|CPU)\s+(model|KV|RS|compute|output)\s+buffer size =\s+([\d.]+) MiB")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def bench(path: Path) -> list:
    rows = read_json(path) or []
    out = []
    for r in rows:
        test = f"pp{r['n_prompt']}" if r["n_prompt"] else f"tg{r['n_gen']}"
        out.append({"test": test, "depth": r.get("n_depth", 0), "ts": round(r["avg_ts"], 4),
                    "sd": round(r["stddev_ts"], 4)})
    return out


def batched(path: Path) -> list:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            rows.append({k: r[k] for k in ("pp", "tg", "pl", "speed_pp", "speed_tg", "t_pp", "t_tg", "speed")})
    return rows


def server_log(path: Path) -> dict:
    if not path.exists():
        return {}
    tasks: dict = {}
    buffers: dict = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TIMING.search(line)
        if m:
            t = tasks.setdefault(int(m.group(1)), {})
            kind = "prompt" if m.group(2) == "prompt eval" else "gen"
            t[f"{kind}_ms"] = float(m.group(3))
            t[f"{kind}_n"] = int(m.group(4))
            continue
        m = DRAFT.search(line)
        if m:
            t = tasks.setdefault(int(m.group(1)), {})
            t.update({"draft_rate": float(m.group(2)), "draft_acc": int(m.group(3)), "draft_gen": int(m.group(4)),
                      "draft_mean_len": float(m.group(5))})
            continue
        m = BUFFER.search(line)
        if m:
            key = f"{m.group(1)} {m.group(2)}"
            buffers[key] = round(buffers.get(key, 0) + float(m.group(3)), 1)
    return {"tasks": [dict(id=k, **v) for k, v in sorted(tasks.items())], "buffers_mib": buffers}


def telemetry(prefix: Path) -> dict:
    out = {}
    gpu = Path(f"{prefix}-gpu.csv")
    if gpu.exists():
        rows = []
        with gpu.open(encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f, skipinitialspace=True):
                try:
                    rows.append({"power": float(r["power_w"]), "temp": float(r["temp_c"]),
                                 "clock": float(r["clock_gr_mhz"]), "util": float(r["util_pct"]),
                                 "mem": float(r["mem_used_mib"])})
                except (ValueError, KeyError, TypeError):
                    continue
        busy = [r for r in rows if r["util"] >= 50] or rows
        if rows:
            out.update({
                "samples": len(rows),
                "power_busy_avg_w": round(statistics.fmean(r["power"] for r in busy), 1),
                "power_max_w": round(max(r["power"] for r in rows), 1),
                "temp_max_c": max(r["temp"] for r in rows),
                "clock_busy_avg_mhz": round(statistics.fmean(r["clock"] for r in busy)),
                "dedicated_used_max_mib": max(r["mem"] for r in rows),
            })
    mem = Path(f"{prefix}-gpumem.csv")
    if mem.exists():
        with mem.open(encoding="utf-8", errors="replace") as f:
            reader = csv.reader(line for line in f if line.strip())  # typeperf starts with a blank line
            header = next(reader, [])
            rows = [r for r in reader if len(r) == len(header)]

            def col_max(i: int) -> float:
                vals = []
                for r in rows:
                    try:
                        vals.append(float(r[i]))
                    except ValueError:
                        pass
                return max(vals, default=0.0)

            # The GPU's adapter LUID changes across reboots: take the adapter with the most dedicated memory in use.
            ded_cols = [i for i, h in enumerate(header) if "Dedicated Usage" in h]
            ded = max(ded_cols, key=col_max, default=None)
            luid = re.search(r"\((luid_[^)]*)\)", header[ded]).group(1) if ded is not None else ""
            sha = next((i for i, h in enumerate(header) if luid and luid in h and "Shared Usage" in h), None)
            avail = next((i for i, h in enumerate(header) if "Available MBytes" in h), None)
            peak_ded = col_max(ded) if ded is not None else 0.0
            peak_sha = col_max(sha) if sha is not None else 0.0
            avail_vals = []
            for r in rows:
                try:
                    avail_vals.append(float(r[avail]))
                except (ValueError, TypeError):
                    pass
            min_avail = min(avail_vals) if avail_vals else None
            # Binary GB, as Task Manager and the NVIDIA App show them.
            out.update({"gpu_dedicated_peak_gb": round(peak_ded / 2**30, 4), "gpu_shared_peak_gb": round(peak_sha / 2**30, 4),
                        "ram_available_min_gb": round(min_avail / 1024, 1) if min_avail is not None else None})
    return out


def suite(folder: Path, key: str) -> dict:
    scenarios = {}
    root = folder / key
    if not root.exists():
        return scenarios
    for res in sorted(root.glob("*/results.json")):
        data = read_json(res)
        if not data:
            continue
        reqs = []
        for r in data.get("requests", []):
            decode = None
            if r.get("ok") and r.get("completion_tokens") and r.get("ttft_s") is not None:
                gen_time = r["latency_s"] - r["ttft_s"]
                if gen_time > 0 and r["completion_tokens"] > 1:
                    decode = round((r["completion_tokens"] - 1) / gen_time, 2)
            reqs.append({"users": r["concurrency"], "ok": r["ok"], "latency": round(r["latency_s"], 3),
                         "ttft": round(r["ttft_s"], 3) if r.get("ttft_s") is not None else None,
                         "prompt_tokens": r.get("prompt_tokens"), "completion_tokens": r.get("completion_tokens"),
                         "decode_tps": decode, "preview": (r.get("response_preview") or "")[:240]})
        summaries = []
        for s in data.get("summaries", []):
            users = s["concurrency"]
            dec = [q["decode_tps"] for q in reqs if q["users"] == users and q["decode_tps"]]
            summaries.append({
                "users": users, "success": s["success"], "requests": s["requests"], "wall_s": round(s["wall_time_s"], 2),
                "agg_tps": s["aggregate_output_tps"], "per_user_tps": s["avg_per_request_tps"],
                "min_user_tps": s["min_per_request_tps"], "max_user_tps": s["max_per_request_tps"],
                "avg_latency": s["avg_latency_s"], "p95_latency": s["p95_latency_s"],
                "avg_ttft": s["avg_ttft_s"], "p95_ttft": s["p95_ttft_s"],
                "decode_tps_avg": round(statistics.fmean(dec), 2) if dec else None,
                "completion_tokens": s["total_completion_tokens"],
            })
        scenarios[res.parent.name] = {"summaries": summaries, "requests": reqs}
    return scenarios


def main() -> int:
    models = rb.load_models()
    dataset = {"machine": {
        "laptop": "ASUS ProArt P16 (H7607BA)",
        "chip": "NVIDIA RTX Spark N1X: 20-core Arm CPU + 6144-core Blackwell GPU (compute capability 12.1)",
        "memory": "128 GB LPDDR5X unified (Windows sees 76.5 GB; 50 GB dedicated to the GPU; CUDA can address 109.7 GiB)",
        "os": "Windows 11 Home 10.0.28000 (Arm64)",
        "driver": "NVIDIA 617.69, CUDA 13.4",
        "runtime": "llama.cpp b11671 (ba3c05f71) CUDA build",
        "power": "AC power, Windows power mode Best performance",
    }, "models": {}, "reference": read_json(HERE / "reference-dgx-spark.json")}
    for key, meta in models.items():
        out = rb.OUT / key
        if not out.exists():
            continue
        entry = {"meta": {k: v for k, v in meta.items() if k not in ("mtp",)},
                 "bench_classic": bench(out / "bench-classic.json"),
                 "bench_sweep": bench(out / "bench-sweep.json"),
                 "batched": batched(out / "batched.jsonl"),
                 "batched_ref": batched(out / "batched-ref.jsonl"),
                 "suite": suite(out / "suite", key),
                 "suite_mtp": suite(out / "suite-mtp", key),
                 "server_suite": server_log(out / "server-suite.log"),
                 "server_mtp": server_log(out / "server-mtp.log"),
                 "telemetry": {p: telemetry(out / f"telemetry-{p}") for p in ("bench", "batched", "suite", "mtp", "ref")
                               if Path(f"{out / f'telemetry-{p}'}-gpu.csv").exists()},
                 # Binary GB, as Task Manager and the NVIDIA App show them.
                 "size_gb": round(sum(f.stat().st_size for f in Path(meta["path"]).parent.glob(
                     Path(meta["path"]).name.replace("00001-of-", "*-of-"))) / 2**30, 4)
                 if Path(meta["path"]).exists() else None}
        dataset["models"][key] = entry
    coding = rb.OUT / "coding"
    if coding.exists():
        # One-shot runs only: the packaged final game (neon-spark-final) is the last follow-up round, not a one-shot.
        dataset["coding"] = {d.name: read_json(d / "stats.json") for d in sorted(coding.iterdir())
                             if (d / "stats.json").exists() and not d.name.endswith("-final")}
    manifest = rb.OUT / "manifest.jsonl"
    if manifest.exists():
        dataset["manifest"] = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    target = rb.OUT / "dataset.json"
    target.write_text(json.dumps(dataset, indent=1), encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size / 1024:.0f} KB), models: {', '.join(dataset['models'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
