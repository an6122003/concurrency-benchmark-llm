import json
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\ProArt\Desktop\Project\bench-tools")
import rtx_spark_bench as rb  # noqa: E402

models = rb.load_models()
key = sys.argv[1] if len(sys.argv) > 1 else "qwen3-4b-2507"
model = models[key]
out = rb.OUT / "_smoke"
out.mkdir(parents=True, exist_ok=True)


def chat(prompt, max_tokens=64, stream=True):
    body = json.dumps({"model": key, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
                       "temperature": 0.2, "stream": stream, "stream_options": {"include_usage": True}}).encode()
    req = urllib.request.Request(rb.BASE_URL + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    first = None
    last = None
    text = []
    with urllib.request.urlopen(req, timeout=600) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            obj = json.loads(line[5:])
            for ch in obj.get("choices", []):
                d = ch.get("delta") or {}
                piece = d.get("content") or d.get("reasoning_content")
                if piece:
                    first = first or time.perf_counter()
                    text.append(piece)
            if obj.get("usage") or obj.get("timings"):
                last = obj
    return time.perf_counter() - t0, (first - t0) if first else None, "".join(text), last


cmd = rb.server_cmd(key, model, mtp=False)
with rb.Server(cmd, out / f"server-{key}.log") as srv:
    rb.save_props(out, key)
    lat, ttft, text, last = chat("Say hello in Vietnamese and English, one line each.")
    print("short:", round(lat, 2), "s ttft", round(ttft, 3), "|", text[:120].replace("\n", " "))
    print("usage:", last.get("usage"), "timings:", json.dumps(last.get("timings")))
    longp = "Summarize these notes. " + ("The team uses local AI for drafting, summarization and code review. " * 600)
    for i in range(2):
        lat, ttft, text, last = chat(longp, max_tokens=16)
        t = last.get("timings", {})
        print(f"long #{i+1}: ttft {ttft:.3f}s prompt_n={t.get('prompt_n')} cache_n={t.get('cache_n')} pp_tps={t.get('prompt_per_second')}")
