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
import json
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
    print(f"\nWrote suite output: {out_dir.resolve()}")
    print(f"- {out_dir / 'suite-manifest.json'}")
    if comparison_rows:
        print(f"- {out_dir / 'suite-comparison.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
