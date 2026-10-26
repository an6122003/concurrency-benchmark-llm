"""One-shot coding test: one prompt, one answer, no follow-ups.

Starts llama-server with the production-style config (reasoning on, optional
speculative decoding), streams the answer, and records every chunk with a
timestamp so the generation can be replayed for video. Writes the extracted
HTML file, the raw reasoning/answer and a stats.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rtx_spark_bench as rb  # noqa: E402
from spec_showdown import CONFIGS as SPEC  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--spec", default="mtp-n2", choices=sorted(SPEC))
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--max-tokens", type=int, default=32000)
    args = parser.parse_args()

    model = rb.load_models()[args.model]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    (out / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    cmd = [str(rb.LLAMA / "llama-server.exe"), "-m", model["path"], "--host", "127.0.0.1", "--port", str(rb.PORT),
           "--alias", args.model, "-ngl", "999", "--fit", "off", "-fa", "on", "-c", "65536", "-np", "1",
           "-b", "2048", "-ub", "2048", "--jinja", "--no-webui", "--metrics",
           "--reasoning", "on", "--reasoning-effort", args.effort] + SPEC[args.spec]
    (out / "server-args.json").write_text(json.dumps(cmd, indent=2), encoding="utf-8")

    events = []
    with rb.Telemetry(out / "telemetry"), rb.Server(cmd, out / "server.log"):
        body = json.dumps({
            "model": args.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": args.max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }).encode("utf-8")
        req = urllib.request.Request(rb.BASE_URL + "/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        final = {}
        with urllib.request.urlopen(req, timeout=7200) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                obj = json.loads(line[5:])
                now = round(time.perf_counter() - t0, 4)
                for choice in obj.get("choices", []):
                    delta = choice.get("delta") or {}
                    for kind in ("reasoning_content", "content"):
                        if delta.get(kind):
                            events.append({"t": now, "kind": "think" if kind == "reasoning_content" else "answer",
                                           "text": delta[kind]})
                    if choice.get("finish_reason"):
                        final["finish_reason"] = choice["finish_reason"]
                if obj.get("usage"):
                    final["usage"] = obj["usage"]
                if obj.get("timings"):
                    final["timings"] = obj["timings"]
        total = time.perf_counter() - t0

    with (out / "stream.jsonl").open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    think = "".join(e["text"] for e in events if e["kind"] == "think")
    answer = "".join(e["text"] for e in events if e["kind"] == "answer")
    (out / "reasoning.md").write_text(think, encoding="utf-8")
    (out / "answer.md").write_text(answer, encoding="utf-8")
    blocks = re.findall(r"```(?:html)?\s*\n(.*?)```", answer, flags=re.S)
    html = max(blocks, key=len) if blocks else answer
    (out / "index.html").write_text(html, encoding="utf-8")

    first = next((e["t"] for e in events), None)
    first_answer = next((e["t"] for e in events if e["kind"] == "answer"), None)
    timings = final.get("timings", {})
    stats = {
        "model": model["label"], "quant": model["quant"], "spec": args.spec, "effort": args.effort,
        "total_s": round(total, 1), "ttft_s": first, "thinking_s": first_answer,
        "answer_s": round(total - first_answer, 1) if first_answer else None,
        "usage": final.get("usage"), "timings": timings, "finish_reason": final.get("finish_reason"),
        "reasoning_chars": len(think), "answer_chars": len(answer), "html_chars": len(html),
        "html_lines": html.count("\n") + 1,
    }
    if timings.get("predicted_n") and timings.get("predicted_ms"):
        stats["decode_tps"] = round(timings["predicted_n"] / (timings["predicted_ms"] / 1000), 2)
    (out / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
