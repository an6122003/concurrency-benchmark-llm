"""Flatten dataset.json into the CSV tables the report charts read.

Writes report-data/*.csv next to dataset.json. Run analyze.py first. Every number
is stored at the precision the report shows it (half-up), so a value on the page
is exactly the value in its source file.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rtx_spark_bench as rb  # noqa: E402

SCENARIO_LABELS = {
    "01_latency_single_user": "Single user, short chat",
    "02_team_concurrency": "Team chat, 1-10 users",
    "03_peak_decode_long_output": "Long answers (1024 tokens)",
    "04_context_4k": "4K-word document",
    "05_context_8k": "8K-word document",
    "06_coding_smoke": "Coding prompts",
    "07_vietnamese_smoke": "Vietnamese prompts",
    "08_extraction_classification": "Extraction and classification",
    "09_context_16k": "16K-word document",
    "10_team_stress": "Team chat, 12-32 users",
}


# Chart labels, short enough to sit beside a bar or at a line's end on a phone.
TINY = {
    "qwen3.8-27b": "Qwen3.8-27B", "qwen3.6-35b-a3b": "Qwen3.6-35B", "nemotron-3.5-super-120b": "Nemotron Super",
    "qwen3.8-flash-next": "Flash-Next", "gemma-4-26b-a4b": "Gemma 4 26B", "nemotron-3.5-nano-30b": "Nemotron Nano",
    "gpt-oss-20b": "gpt-oss-20b", "qwen3-4b-2507": "Qwen3-4B", "gemma-4-e4b": "Gemma 4 E4B",
}


def fx(x, nd: int = 1):
    """Round half-up on the decimal text (33.05 -> 33.1); nd=0 gives an int."""
    if x is None or x == "":
        return None
    q = Decimal(str(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return int(q) if nd == 0 else float(q)


def tps(test: str, v):
    """Prefill (pp) as whole tok/s, decode (tg) to one decimal."""
    return fx(v, 0) if test.startswith("pp") else fx(v, 1)


def write(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.unlink(missing_ok=True)  # no stale table from an earlier run
        return
    cols = list(rows[0].keys())
    for r in rows[1:]:
        cols += [k for k in r if k not in cols]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"{path.name}: {len(rows)} rows")


def main() -> int:
    data = json.loads((rb.OUT / "dataset.json").read_text(encoding="utf-8"))
    out = rb.OUT / "report-data"
    out.mkdir(exist_ok=True)
    models, bench, batched, conc, context, power = [], [], [], [], [], []
    for key, m in data["models"].items():
        meta = m["meta"]
        label = meta["label"]
        models.append({"model": key, "label": label, "short": re.sub(r"\s*\(.*\)$", "", label), "tiny": TINY.get(key, key),
                       "family": meta["family"], "kind": meta["kind"], "params_b": meta["params_b"],
                       "active_b": meta["active_b"], "quant": meta["quant"], "size_gb": fx(m.get("size_gb"), 1),
                       "released": meta["released"], "source": meta["source"]})
        for kind, rows in (("classic", m["bench_classic"]), ("sweep", m["bench_sweep"])):
            for r in rows:
                bench.append({"model": key, "label": label, "set": kind, "test": r["test"], "depth": r["depth"],
                              "tps": tps(r["test"], r["ts"]), "sd": tps(r["test"], r["sd"])})
        for r in m["batched"]:
            batched.append({"model": key, "label": label, "parallel": r["pl"], "decode_tps": fx(r["speed_tg"], 1),
                            "per_stream_tps": fx(r["speed_tg"] / r["pl"], 1), "prefill_tps": fx(r["speed_pp"], 0)})
        for mode, suite in (("baseline", m["suite"]), ("mtp", m["suite_mtp"])):
            for scen, body in suite.items():
                for s in body["summaries"]:
                    conc.append({"model": key, "label": label, "mode": mode, "scenario": scen,
                                 "scenario_label": SCENARIO_LABELS.get(scen, scen), "users": s["users"],
                                 "success": s["success"], "requests": s["requests"],
                                 "agg_tps": fx(s["agg_tps"] or 0, 1), "per_user_tps": fx(s["per_user_tps"] or 0, 1),
                                 "min_user_tps": fx(s["min_user_tps"] or 0, 1), "decode_tps": fx(s["decode_tps_avg"], 1),
                                 "avg_ttft_s": fx(s["avg_ttft"] or 0, 2), "p95_ttft_s": fx(s["p95_ttft"] or 0, 2),
                                 "avg_latency_s": fx(s["avg_latency"] or 0, 1), "p95_latency_s": fx(s["p95_latency"] or 0, 1)})
                if mode == "baseline" and scen in ("04_context_4k", "05_context_8k", "09_context_16k"):
                    for q in body["requests"]:
                        if q["ok"] and q["users"] == 1 and q["ttft"]:
                            context.append({"model": key, "label": label, "scenario": scen,
                                            "scenario_label": SCENARIO_LABELS[scen], "prompt_tokens": q["prompt_tokens"],
                                            "ttft_s": fx(q["ttft"], 2),
                                            "prefill_tps": fx(q["prompt_tokens"] / q["ttft"], 0) if q["prompt_tokens"] else None,
                                            "decode_tps": fx(q["decode_tps"], 1)})
        for phase, t in m["telemetry"].items():
            power.append({"model": key, "label": label, "phase": phase,
                          **{k: fx(v, 1) if k.endswith("_gb") else v for k, v in t.items()}})
    write(out / "models.csv", models)
    write(out / "llama_bench.csv", bench)
    write(out / "batched.csv", batched)
    write(out / "concurrency.csv", conc)
    write(out / "context.csv", context)
    write(out / "power.csv", power)

    ref = data.get("reference") or {}
    ref_rows = []
    for test, series in (ref.get("llama_bench", {}).get("gpt-oss-20b", {})).items():
        for depth, v in series.items():
            ref_rows.append({"machine": "DGX Spark", "test": test, "depth": int(depth), "tps": tps(test, v)})
    gpt = data["models"].get("gpt-oss-20b")
    if gpt:
        for r in gpt["bench_sweep"]:
            ref_rows.append({"machine": "RTX Spark laptop", "test": r["test"], "depth": r["depth"], "tps": tps(r["test"], r["ts"])})
    write(out / "reference.csv", ref_rows)

    spec = rb.OUT / "spec-showdown" / "qwen3.8-27b.json"
    if spec.exists():
        s = json.loads(spec.read_text(encoding="utf-8"))
        names = {"none": "No speculation", "mtp-n2": "MTP, 2 drafts", "mtp-n3": "MTP, 3 drafts", "dflash2": "DFlash2 draft model"}
        write(out / "spec.csv", [{"config": name, "config_label": names.get(name, name), "gen_tps": fx(r["gen_tps_mean"], 1),
                                  "acceptance_pct": fx(r["acceptance_mean"] * 100, 0) if r["acceptance_mean"] else None,
                                  "html_tps": fx(r["gen_tps_by_prompt"][0], 1), "python_tps": fx(r["gen_tps_by_prompt"][1], 1),
                                  "prose_tps": fx(r["gen_tps_by_prompt"][2], 1), "best": name == s["best"]}
                                 for name, r in s["results"].items()])
    coding = []
    apps = {"neon-spark": "NEON SPARK (arcade game)", "galaxy-forge": "Galaxy Forge (web app)"}
    for run, st in (data.get("coding") or {}).items():
        if not st:
            continue
        usage = st.get("usage") or {}
        coding.append({"run": run, "app": apps.get(run, run), "model": st["model"], "spec": st["spec"], "effort": st["effort"],
                       "total_min": fx(st["total_s"] / 60, 1), "thinking_min": fx((st.get("thinking_s") or 0) / 60, 1),
                       "writing_min": fx((st.get("answer_s") or 0) / 60, 1), "completion_tokens": usage.get("completion_tokens"),
                       "prompt_tokens": usage.get("prompt_tokens"), "decode_tps": fx(st.get("decode_tps"), 1),
                       "html_lines": st.get("html_lines"), "html_kb": fx(st.get("html_chars", 0) / 1024, 1),
                       "finish": st.get("finish_reason")})
    write(out / "coding.csv", coding)
    battery = json.loads((HERE / "battery-datapoint.json").read_text(encoding="utf-8"))
    write(out / "battery.csv", [{"power_id": "battery" if r["power"].startswith("Battery") else "charger", **r,
                                 "tps": tps(r["test"], r["tps"]), "sd": tps(r["test"], r["sd"])} for r in battery["rows"]])
    write(out / "facts.csv", facts())
    write(out / "phases.csv", phase_rows(data.get("manifest") or []))
    write(out / "vram_ab.csv", vram_ab())
    write(out / "iteration.csv", iteration_rows())
    shared = rb.OUT / "shared-memory-test" / "results.json"
    if shared.exists():
        rows = json.loads(shared.read_text(encoding="utf-8-sig"))
        write(out / "shared_test.csv", [{**r, "pp512": fx(r["pp512"], 0), "tg128": fx(r["tg128"], 2)} for r in rows])
    return 0


# The 65 W charger was swapped for a 140 W one while the work was paused on the morning of 26 October.
CHARGER_140W_FROM = "2026-10-26T09:00"
PHASE_LABELS = {"bench": "llama-bench", "quick": "llama-bench (quick)", "suite": "Concurrency suite", "team": "Team chat suite",
                "mtp": "Suite with MTP", "batched": "Batched decode", "ref": "DGX reference run"}


def phase_rows(manifest: list[dict]) -> list[dict]:
    """Every finished GPU phase with its charger and the battery level at its start and end."""
    rows = []
    for e in manifest:
        if e.get("status") != "ok" or "power_start" not in e:
            continue
        b0, b1 = e["power_start"]["battery_pct"], e["power_end"]["battery_pct"]
        rows.append({"phase_id": f"{e['model']}:{e['phase']}:{e.get('tag', '')}", "model": e["model"],
                     "phase": PHASE_LABELS.get(e["phase"], e["phase"]), "tag": e.get("tag", ""), "started": e["started"],
                     "charger": "140 W" if e["started"] >= CHARGER_140W_FROM else "65 W", "minutes": fx(e["duration_s"] / 60, 1),
                     "battery_start": b0, "battery_end": b1, "battery_change": b1 - b0})
    return rows


def facts() -> list[dict]:
    """Measured setup facts the report quotes in its text, each read from its own evidence file."""
    import gguf_tensors  # noqa: E402 - sibling module, imported lazily
    rows = []
    log = (rb.OUT / "evidence" / "vram-50gb-nemotron-3.5-super.txt").read_text(encoding="utf-8-sig")
    mib = int(re.search(r"CUDA can address: .*?\((\d+) MiB", log).group(1))
    rows.append({"fact": "cuda_addressable_gb", "value": fx(mib / 1024, 1), "unit": "GB",
                 "note": "GPU memory CUDA reports at the 50 GB setting, dedicated plus shared (evidence/vram-50gb-nemotron-3.5-super.txt)"})
    shards = sorted(Path(rb.load_models()["qwen3.8-flash-next"]["path"]).parent.glob("Qwen3.8-Flash-Next-UD-IQ4_XS-*-of-*.gguf"))
    embd = sum(n for s in shards for name, _, n in gguf_tensors.tensors(str(s)) if name.startswith("per_layer_token_embd"))
    rows.append({"fact": "flash_next_embd_gb", "value": fx(embd / 2**30, 1), "unit": "GB",
                 "note": "Qwen3.8-Flash-Next per-layer embedding table, which llama.cpp keeps in system RAM (GGUF headers)"})
    return rows


# What each NEON SPARK prompt asked for, in a line (the full text is prompt.txt / feedback.txt in each folder).
ASKED = {
    "neon-spark": "A visually stunning synthwave arcade game in one HTML file",
    "v2": "Fix waves jumping to the boss and the score stuck at 0; striped sun; punchier explosions, combo, title intro",
    "v3": "Story intro, three sectors with bosses, upgrade cards, Overdrive, victory screen and Hard mode",
    "v4": "Premium polish: boss HUD, card icons and levels, cinematic intro, sector tally, tougher enemies, music per sector",
    "v5": "Bring back the HUD (a console error hid it), boss defeat lines and break-apart deaths, upgrade levels, bigger cards",
    "v6": "Visual polish: keep the defeat line on screen, a glowing death burst, readable boss names, correct level bars",
    "v7": "Free movement (up and down too), and phone portrait: stacked upgrade cards, wrapped intro, defeat lines and epilogue",
    "v8": "Layout fixes: centered intro on monitors, intro below its header on phones, phone cards that hold their text",
    "v9": "Fix an audio console error, lay out phone cards icon-left so text stays inside, one typing cursor on phones",
    "v10": "Polish the phone upgrade cards: compact, centered, with their level label",
}


def iteration_rows() -> list[dict]:
    """NEON SPARK from the one-shot prompt through each follow-up round, all on the same local model."""
    coding = rb.OUT / "coding"
    marker = coding / "neon-spark-final" / "version.txt"
    final = int(marker.read_text(encoding="utf-8").strip()[1:]) if marker.exists() else None
    versions = sorted((p for p in (coding / "neon-spark-iterated").glob("v*") if final is None or int(p.name[1:]) <= final),
                      key=lambda p: int(p.name[1:]))
    runs = [("Prompt 1 (one-shot)", coding / "neon-spark")]
    runs += [(f"Prompt {p.name[1:]} ({'final' if int(p.name[1:]) == final else 'follow-up'})", p) for p in versions]
    rows = []
    for label, folder in runs:
        stats = folder / "stats.json"
        if not stats.exists():
            continue
        s = json.loads(stats.read_text(encoding="utf-8"))
        usage = s.get("usage") or {}
        rows.append({"round": label, "folder": folder.name, "asked": ASKED.get(folder.name, ""), "prompt_tokens": usage.get("prompt_tokens"),
                     "completion_tokens": usage.get("completion_tokens"), "total_min": fx(s["total_s"] / 60, 1),
                     "thinking_min": fx((s.get("thinking_s") or 0) / 60, 1), "decode_tps": fx(s.get("decode_tps"), 1),
                     "html_lines": s.get("html_lines"), "html_kb": fx(s.get("html_chars", 0) / 1024, 1)})
    return rows


def vram_ab() -> list[dict]:
    """50 GB vs 96 GB GPU memory setting: every quick llama-bench run of the two big models."""
    import analyze  # noqa: E402 - sibling module, imported lazily
    runs = [
        ("nemotron-3.5-super-120b", 50, "nemotron-3.5-super-120b-gpu50", "bench-quick.json", "telemetry-quick", "quick", True),
        ("nemotron-3.5-super-120b", 96, "nemotron-3.5-super-120b-gpu96", "bench-quick.json", "telemetry-quick", "quick, first run after reboot", False),
        ("nemotron-3.5-super-120b", 96, "nemotron-3.5-super-120b", "bench-classic.json", "telemetry-bench", "classic", True),
        ("nemotron-3.5-super-120b", 96, "nemotron-3.5-super-120b-gpu96", "bench-quick-repeat2.json", None, "repeat 2", True),
        ("nemotron-3.5-super-120b", 96, "nemotron-3.5-super-120b-gpu96", "bench-quick-repeat3.json", None, "repeat 3", True),
        ("qwen3.8-flash-next", 50, "qwen3.8-flash-next-gpu50", "bench-quick-eager.json", None, "CUDA_MODULE_LOADING=EAGER (default crashed)", True),
        ("qwen3.8-flash-next", 96, "qwen3.8-flash-next-gpu96", "bench-quick.json", "telemetry-quick", "quick, Windows RAM exhausted", True),
    ]
    rows = []
    for i, (model, setting, folder, name, tele, note, used) in enumerate(runs):
        path = rb.OUT / folder / name
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        t = analyze.telemetry(rb.OUT / folder / tele) if tele else {}
        rows.append({"run_id": f"r{i + 1}", "model": model, "setting_gb": setting, "run": note, "in_average": used,
                     "pp512": fx(next(r["avg_ts"] for r in data if r["n_prompt"]), 0),
                     "tg128": fx(next(r["avg_ts"] for r in data if r["n_gen"]), 2),
                     "dedicated_gb": fx(t.get("gpu_dedicated_peak_gb"), 1), "shared_gb": fx(t.get("gpu_shared_peak_gb"), 1),
                     "ram_free_min_gb": fx(t.get("ram_available_min_gb"), 1)})
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
