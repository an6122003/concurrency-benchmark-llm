"""Speculative decoding showdown for one model: none vs MTP vs DFlash2.

Single user, long code output, the model's own sampling defaults (as in the
one-shot coding test). Writes spec-showdown/<model>.json and prints the
fastest configuration.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rtx_spark_bench as rb  # noqa: E402

CONFIGS = {
    "none": [],
    "mtp-n2": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2"],
    "mtp-n3": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "3"],
    "dflash2": ["--spec-type", "draft-dflash", "-md",
                r"C:\Users\ProArt\.cache\huggingface\hub\models--incoai--Qwen3.8-27B-DFlash2-GGUF\snapshots"
                r"\144eb06583b4fb0b6e54bc814b16a206a240f4d2\Qwen3.8-27B-DFlash2-Q4_K_M.gguf"],
}
PROMPTS = [
    "Write a complete single-file HTML page with an animated canvas starfield and a glowing title. Return only the code.",
    "Write a Python module that implements an LRU cache with TTL expiry, type hints, docstrings and unit tests. Return only the code.",
    "Explain, in about 300 words, how speculative decoding speeds up LLM inference, for a non-technical audience.",
]


def main() -> int:
    key = sys.argv[1] if len(sys.argv) > 1 else "qwen3.8-27b"
    configs = sys.argv[2].split(",") if len(sys.argv) > 2 else list(CONFIGS)
    model = rb.load_models()[key]
    out = rb.OUT / "spec-showdown"
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in configs:
        cmd = [str(rb.LLAMA / "llama-server.exe"), "-m", model["path"], "--host", "127.0.0.1", "--port", str(rb.PORT),
               "--alias", key, "-ngl", "999", "--fit", "off", "-fa", "on", "-c", "16384", "-np", "1",
               "--no-cache-prompt", "--jinja", "--no-webui", "--reasoning", "off"] + CONFIGS[name]
        runs = []
        with rb.Telemetry(out / f"telemetry-{key}-{name}"), rb.Server(cmd, out / f"server-{key}-{name}.log"):
            for rep in range(2):
                for i, prompt in enumerate(PROMPTS):
                    body = json.dumps({"model": key, "messages": [{"role": "user", "content": prompt}],
                                       "max_tokens": 768, "stream": False}).encode("utf-8")
                    req = urllib.request.Request(rb.BASE_URL + "/v1/chat/completions", data=body,
                                                 headers={"Content-Type": "application/json"})
                    t0 = time.perf_counter()
                    with urllib.request.urlopen(req, timeout=900) as resp:
                        obj = json.loads(resp.read().decode("utf-8"))
                    t = obj.get("timings", {})
                    runs.append({"rep": rep, "prompt": i, "wall_s": round(time.perf_counter() - t0, 2),
                                 "gen_n": t.get("predicted_n"), "gen_tps": round(t.get("predicted_per_second", 0), 2),
                                 "prompt_tps": round(t.get("prompt_per_second", 0), 1),
                                 "draft_n": t.get("draft_n"), "draft_accepted": t.get("draft_n_accepted")})
                    rb.log(f"{name} rep{rep} p{i}: {runs[-1]}")
        tps = [r["gen_tps"] for r in runs]
        acc = [r["draft_accepted"] / r["draft_n"] for r in runs if r.get("draft_n")]
        results[name] = {"runs": runs, "gen_tps_mean": round(statistics.fmean(tps), 2),
                         "gen_tps_by_prompt": [round(statistics.fmean(r["gen_tps"] for r in runs if r["prompt"] == i), 2)
                                               for i in range(len(PROMPTS))],
                         "acceptance_mean": round(statistics.fmean(acc), 3) if acc else None}
    best = max(results, key=lambda n: results[n]["gen_tps_mean"])
    payload = {"model": key, "prompts": PROMPTS, "results": results, "best": best}
    (out / f"{key}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for name, r in results.items():
        rb.log(f"{name}: {r['gen_tps_mean']} tok/s (by prompt {r['gen_tps_by_prompt']}, acceptance {r['acceptance_mean']})")
    print(f"BEST={best}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
