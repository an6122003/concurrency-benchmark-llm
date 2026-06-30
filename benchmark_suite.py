#!/usr/bin/env python3
"""
Run a repeatable multi-scenario local LLM benchmark suite.

This orchestrates ai_concurrent_benchmark.py and writes a suite manifest plus
comparison CSV for later spreadsheet/database import.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


PROMPT_BLOCKS = {
    "short_chat": [
        "In Vietnamese, explain whether a 32GB GPU can serve a small AI team. Keep it practical.",
        "Summarize the tradeoff between local AI and cloud AI in five bullets.",
        "Draft a friendly answer to a teammate asking why local LLM speed drops with concurrent users.",
    ],
    "coding": [
        "Write a Python function that groups benchmark rows by hardware model and returns average tokens per second.",
        "Review this API design idea: one endpoint uploads benchmark JSON and one endpoint searches hardware results. Suggest improvements.",
    ],
    "vietnamese": [
        "Viết một đoạn giải thích dễ hiểu về TTFT, latency và tokens/second cho người mới dùng AI local.",
        "Tóm tắt ưu nhược điểm của việc dùng một máy local AI server cho team 5 người.",
    ],
    "classification": [
        "Classify each item as bug, feature request, pricing concern, or praise: app crashes on upload; add CSV export; too expensive; love the UI.",
        "Extract hardware model, runtime, quantization, and concurrency count from: RTX 4090, Ollama CUDA, Qwen 32B Q4_K_M, 6 users.",
    ],
}


def repeated_prompt(label: str, approx_words: int) -> str:
    base = (
        f"{label}: You are benchmarking long-context behavior for a local LLM server. "
        "Read the following synthetic project notes and answer with a concise summary, risks, and action items. "
    )
    filler = (
        "The team uses local AI for drafting, summarization, customer feedback classification, code review, "
        "Vietnamese content ideation, and document Q&A. The benchmark should capture responsiveness, throughput, "
        "context pressure, memory headroom, and stability under concurrent sessions. "
    )
    words: List[str] = base.split()
    filler_words = filler.split()
    while len(words) < approx_words:
        words.extend(filler_words)
    return " ".join(words[:approx_words])


def write_prompts(path: Path, prompts: List[str]) -> None:
    path.write_text("\n---\n".join(prompts), encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_prompts(scenario: Dict[str, Any]) -> List[str]:
    prompt_set = scenario.get("prompt_set", "short_chat")
    if prompt_set == "context":
        words = int(scenario.get("approx_prompt_words", 2000))
        return [repeated_prompt(scenario["name"], words)]
    return PROMPT_BLOCKS.get(prompt_set, PROMPT_BLOCKS["short_chat"])


def build_command(
    python_bin: str,
    repo_dir: Path,
    target: Dict[str, Any],
    scenario: Dict[str, Any],
    prompt_file: Path,
    out_dir: Path,
) -> List[str]:
    cmd = [
        python_bin,
        str(repo_dir / "ai_concurrent_benchmark.py"),
        "--server", target["server"],
        "--base-url", target["base_url"],
        "--model", target["model"],
        "--concurrency", scenario["concurrency"],
        "--max-tokens", str(scenario["max_tokens"]),
        "--temperature", str(scenario.get("temperature", target.get("temperature", 0.2))),
        "--timeout", str(scenario.get("timeout", target.get("timeout", 900))),
        "--cooldown", str(scenario.get("cooldown", 1)),
        "--warmup", str(scenario.get("warmup", 1)),
        "--warmup-tokens", str(scenario.get("warmup_tokens", 64)),
        "--warmup-pause", str(scenario.get("warmup_pause", 1)),
        "--prompts-file", str(prompt_file),
        "--out-dir", str(out_dir),
    ]
    optional_map = {
        "--runtime": target.get("runtime"),
        "--gpu": target.get("gpu"),
        "--quantization": target.get("quantization"),
        "--context-size": target.get("context_size"),
        "--notes": target.get("notes"),
        "--hardware-image": target.get("hardware_image"),
    }
    for flag, value in optional_map.items():
        if value is not None and value != "":
            cmd.extend([flag, str(value)])
    return cmd


def summarize_result(result_path: Path, suite_name: str, target_name: str, scenario_name: str) -> List[Dict[str, Any]]:
    data = load_json(result_path)
    meta = data.get("meta", {})
    config = meta.get("benchmark_config", {})
    rows = []
    for summary in data.get("summaries", []):
        rows.append({
            "suite": suite_name,
            "target": target_name,
            "scenario": scenario_name,
            "model": config.get("model"),
            "hardware": config.get("gpu_label") or (meta.get("gpu", {}).get("detected", [{}])[0].get("name")),
            "runtime": config.get("runtime_label") or config.get("server"),
            "quantization": config.get("model_quantization"),
            "context_size": config.get("context_size"),
            "max_tokens": config.get("max_tokens_per_request"),
            "concurrency": summary.get("concurrency"),
            "success": summary.get("success"),
            "requests": summary.get("requests"),
            "aggregate_output_tps": summary.get("aggregate_output_tps"),
            "avg_per_request_tps": summary.get("avg_per_request_tps"),
            "avg_latency_s": summary.get("avg_latency_s"),
            "p95_latency_s": summary.get("p95_latency_s"),
            "avg_ttft_s": summary.get("avg_ttft_s"),
            "result_json": str(result_path),
        })
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fmt(value: Any, digits: int = 2) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def copy_brand_assets(out_dir: Path, repo_dir: Path) -> None:
    source_dir = repo_dir / "assets" / "techieslab"
    target_dir = out_dir / "assets" / "techieslab"
    if not source_dir.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.glob("*.png"):
        shutil.copyfile(source, target_dir / source.name)


def best_rows(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    successful = [row for row in rows if number(row.get("success")) == number(row.get("requests"))]
    return {
        "throughput": max(rows, key=lambda row: number(row.get("aggregate_output_tps")), default={}),
        "per_user": max(rows, key=lambda row: number(row.get("avg_per_request_tps")), default={}),
        "latency": min([row for row in rows if row.get("p95_latency_s") is not None], key=lambda row: number(row.get("p95_latency_s")), default={}),
        "ttft": min([row for row in rows if row.get("avg_ttft_s") is not None], key=lambda row: number(row.get("avg_ttft_s")), default={}),
        "comfort": max(successful, key=lambda row: number(row.get("concurrency")), default={}),
    }


def write_suite_html(path: Path, manifest: Dict[str, Any], rows: List[Dict[str, Any]], dense: bool = False) -> None:
    suite_name = manifest.get("suite_name", "local-llm-suite")
    best = best_rows(rows)
    scenarios = sorted({str(row.get("scenario")) for row in rows})
    targets = sorted({str(row.get("target")) for row in rows})
    chart_rows = [
        row for row in rows
        if row.get("scenario") == best.get("throughput", {}).get("scenario")
    ] or rows
    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('target') or ''))}</td>"
        f"<td>{html.escape(str(row.get('scenario') or ''))}</td>"
        f"<td>{html.escape(str(row.get('model') or ''))}</td>"
        f"<td>{html.escape(str(row.get('hardware') or ''))}</td>"
        f"<td>{html.escape(str(row.get('runtime') or ''))}</td>"
        f"<td>{html.escape(str(row.get('quantization') or ''))}</td>"
        f"<td>{row.get('concurrency')}</td>"
        f"<td>{row.get('success')}/{row.get('requests')}</td>"
        f"<td>{fmt(row.get('aggregate_output_tps'))}</td>"
        f"<td>{fmt(row.get('avg_per_request_tps'))}</td>"
        f"<td>{fmt(row.get('avg_ttft_s'))}</td>"
        f"<td>{fmt(row.get('p95_latency_s'))}</td>"
        f"<td><a href=\"{html.escape(str(Path(row.get('result_json', '')).parent / 'report.html'))}\">report</a></td>"
        "</tr>"
        for row in rows
    )
    chart_payload = {
        "labels": [f"{row.get('target')} · {row.get('concurrency')}u" for row in chart_rows],
        "aggregate": [number(row.get("aggregate_output_tps")) for row in chart_rows],
        "perUser": [number(row.get("avg_per_request_tps")) for row in chart_rows],
        "ttft": [number(row.get("avg_ttft_s")) for row in chart_rows],
        "p95": [number(row.get("p95_latency_s")) for row in chart_rows],
    }
    stat_cards = [
        ("Targets", str(len(targets))),
        ("Scenarios", str(len(scenarios))),
        ("Best throughput", f"{fmt(best['throughput'].get('aggregate_output_tps'))} tok/s"),
        ("Comfortable users", f"{best['comfort'].get('concurrency', '-')} users"),
        ("Lowest TTFT", f"{fmt(best['ttft'].get('avg_ttft_s'))} s"),
        ("Lowest P95", f"{fmt(best['latency'].get('p95_latency_s'))} s"),
    ]
    cards = "\n".join(f"<div class=\"stat\"><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong></div>" for k, v in stat_cards)
    title = "Suite Comparison" if dense else "Suite Report"
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · {html.escape(suite_name)}</title>
  <link rel="icon" href="assets/techieslab/avatar.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..700;1,400..600&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{ --bg:#0a0a14; --surface:#15132a; --surface2:#1c1936; --violet:#8070f8; --violet-l:#a090f8; --cyan:#58c8f8; --mint:#60d8c0; --white:#fff; --dim:rgba(255,255,255,.68); --faint:rgba(255,255,255,.42); --line:rgba(255,255,255,.1); --sans:"Inter",-apple-system,system-ui,sans-serif; --serif:"EB Garamond",Georgia,serif; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:var(--sans); color:var(--white); background:linear-gradient(rgba(10,10,20,.88),rgba(10,10,20,.96)),url("assets/techieslab/background.png") top center / min(100vw,1800px) auto no-repeat,var(--bg); }}
    main {{ max-width:1320px; margin:0 auto; padding:24px; }}
    .brandbar {{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:24px; }}
    .brand {{ display:flex; align-items:center; gap:12px; }}
    .brand img {{ width:42px; height:42px; border-radius:8px; border:1px solid var(--line); }}
    .brand-name {{ font-family:var(--serif); font-size:1.4rem; }}
    .brand-name span {{ color:var(--violet-l); }}
    h1 {{ font-family:var(--serif); font-weight:400; font-size:clamp(2.4rem,5vw,4.5rem); line-height:1; margin:0 0 12px; }}
    h1 em {{ color:var(--violet-l); }}
    p {{ color:var(--dim); }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:20px 0; }}
    .stat,.panel {{ background:linear-gradient(160deg,rgba(21,19,42,.92),rgba(14,13,28,.92)); border:1px solid var(--line); border-radius:8px; }}
    .stat {{ padding:14px; }}
    .stat span {{ display:block; color:var(--faint); font-size:.76rem; margin-bottom:6px; }}
    .stat strong {{ font-size:1.15rem; }}
    .grid {{ display:grid; grid-template-columns:1.25fr .9fr; gap:16px; }}
    .panel {{ padding:16px; margin-top:16px; }}
    .chart {{ height:340px; }}
    table {{ width:100%; border-collapse:collapse; min-width:1120px; }}
    .table-wrap {{ overflow:auto; }}
    th,td {{ border-bottom:1px solid var(--line); padding:9px; text-align:right; font-size:.84rem; }}
    th {{ color:var(--faint); background:rgba(28,25,54,.92); }}
    td:first-child,th:first-child,td:nth-child(2),th:nth-child(2),td:nth-child(3),th:nth-child(3),td:nth-child(4),th:nth-child(4) {{ text-align:left; }}
    a {{ color:var(--violet-l); }}
    .note {{ border:1px solid rgba(160,144,248,.38); border-radius:8px; padding:14px; background:rgba(128,112,248,.10); }}
    @media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<main>
  <div class="brandbar"><div class="brand"><img src="assets/techieslab/avatar.png" alt=""><div class="brand-name">techies<span>.lab</span></div></div><div>{html.escape(title)}</div></div>
  <h1>{'Detailed <em>comparison</em> table.' if dense else 'All-around <em>benchmark</em> suite.'}</h1>
  <p>{html.escape(suite_name)} · {len(rows)} measured rows · {len(targets)} target(s) · {len(scenarios)} scenario(s)</p>
  <section class="stats">{cards}</section>
  <section class="note">
    This report is intended for hardware/model conclusions and sales solution architecture. Use the per-scenario reports for raw evidence, and use the suite comparison table for buyer-facing tradeoffs: responsiveness, team serving capacity, sustained throughput, context pressure, and software stack compatibility.
  </section>
  <section class="grid">
    <div class="panel"><h2>Throughput / per-user speed</h2><div class="chart"><canvas id="throughput"></canvas></div></div>
    <div class="panel"><h2>Latency / TTFT</h2><div class="chart"><canvas id="latency"></canvas></div></div>
  </section>
  <section class="panel">
    <h2>Scenario comparison</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Target</th><th>Scenario</th><th>Model</th><th>Hardware</th><th>Runtime</th><th>Quant</th><th>Users</th><th>Success</th><th>Aggregate tok/s</th><th>Per-user tok/s</th><th>TTFT</th><th>P95 latency</th><th>Report</th></tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
  </section>
</main>
<script>
Chart.defaults.color = 'rgba(255,255,255,.72)';
Chart.defaults.borderColor = 'rgba(255,255,255,.08)';
const data = {json.dumps(chart_payload)};
new Chart(document.getElementById('throughput'), {{
  type:'bar',
  data:{{labels:data.labels,datasets:[
    {{label:'Aggregate tok/s',data:data.aggregate,backgroundColor:'#8070f8'}},
    {{label:'Per-user tok/s',data:data.perUser,backgroundColor:'#60d8c0'}}
  ]}},
  options:{{maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}}}},scales:{{x:{{ticks:{{maxRotation:45,minRotation:0}}}},y:{{beginAtZero:true}}}}}}
}});
new Chart(document.getElementById('latency'), {{
  type:'line',
  data:{{labels:data.labels,datasets:[
    {{label:'TTFT (s)',data:data.ttft,borderColor:'#58c8f8',backgroundColor:'#58c8f8',tension:.25}},
    {{label:'P95 latency (s)',data:data.p95,borderColor:'#a090f8',backgroundColor:'#a090f8',tension:.25}}
  ]}},
  options:{{maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}}}},scales:{{y:{{beginAtZero:true}}}}}}
}});
</script>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an all-around local LLM benchmark suite.")
    parser.add_argument("--config", default="suite-config.example.json", help="Suite JSON config.")
    parser.add_argument("--out-dir", default=f"suite-results-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_dir = Path(__file__).resolve().parent
    config = load_json(Path(args.config))
    suite_name = config.get("suite_name", "local-llm-suite")
    out_dir = Path(args.out_dir)
    prompt_dir = out_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "suite_name": suite_name,
        "started_at": dt.datetime.now().isoformat(timespec="seconds"),
        "config": config,
        "runs": [],
    }
    comparison_rows: List[Dict[str, Any]] = []

    for target in config.get("targets", []):
        target_name = target.get("name") or target["model"]
        for scenario in config.get("scenarios", []):
            scenario_name = scenario["name"]
            run_dir = out_dir / target_name.replace(" ", "_") / scenario_name
            prompt_file = prompt_dir / f"{scenario_name}.txt"
            write_prompts(prompt_file, scenario_prompts(scenario))
            cmd = build_command(args.python, repo_dir, target, scenario, prompt_file, run_dir)
            manifest["runs"].append({
                "target": target_name,
                "scenario": scenario_name,
                "command": cmd,
                "out_dir": str(run_dir),
            })
            print(f"\n=== {target_name} / {scenario_name} ===")
            print(" ".join(cmd))
            if not args.dry_run:
                subprocess.run(cmd, check=True)
                comparison_rows.extend(summarize_result(run_dir / "results.json", suite_name, target_name, scenario_name))

    manifest["finished_at"] = dt.datetime.now().isoformat(timespec="seconds")
    (out_dir / "suite-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_csv(out_dir / "suite-comparison.csv", comparison_rows)
    if comparison_rows:
        copy_brand_assets(out_dir, repo_dir)
        write_suite_html(out_dir / "suite-report.html", manifest, comparison_rows, dense=False)
        write_suite_html(out_dir / "suite-comparison.html", manifest, comparison_rows, dense=True)
    print(f"\nWrote suite output: {out_dir.resolve()}")
    print(f"- {out_dir / 'suite-manifest.json'}")
    if comparison_rows:
        print(f"- {out_dir / 'suite-comparison.csv'}")
        print(f"- {out_dir / 'suite-report.html'}")
        print(f"- {out_dir / 'suite-comparison.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
