"""Quick functional check of speculative decoding variants for Qwen3.8-27B (port 8098)."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\Users\ProArt\Desktop\Project\bench-tools")
import rtx_spark_bench as rb  # noqa: E402
import oneshot_coding as oc  # noqa: E402

PORT = 8098
URL = f"http://127.0.0.1:{PORT}"
model = rb.load_models()["qwen3.8-27b"]
scratch = Path(sys.argv[0]).resolve().parent
PROMPT = "Write a Python function that parses an ISO-8601 duration string like P1DT2H30M into total seconds, with docstring and 3 doctest examples."

for spec in sys.argv[1:]:
    cmd = [str(rb.LLAMA / "llama-server.exe"), "-m", model["path"], "--host", "127.0.0.1", "--port", str(PORT),
           "-ngl", "999", "--fit", "off", "-fa", "on", "-c", "16384", "-np", "1", "--jinja", "--no-webui",
           "--reasoning", "off"] + oc.SPEC[spec]
    logf = open(scratch / f"spec-{spec}.log", "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, cwd=str(rb.LLAMA))
    try:
        for _ in range(300):
            if proc.poll() is not None:
                raise RuntimeError(f"server exited {proc.returncode}")
            try:
                with urllib.request.urlopen(URL + "/health", timeout=3) as r:
                    if r.status == 200:
                        break
            except OSError:
                pass
            time.sleep(1)
        results = []
        for i in range(2):
            body = json.dumps({"messages": [{"role": "user", "content": PROMPT}], "max_tokens": 400,
                               "temperature": 0.2, "stream": False}).encode()
            req = urllib.request.Request(URL + "/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                obj = json.loads(r.read())
            t = obj.get("timings", {})
            results.append((t.get("predicted_n"), round(t.get("predicted_per_second", 0), 2), t.get("draft_n"), t.get("draft_n_accepted")))
        print(spec, results, flush=True)
    except Exception as exc:  # noqa: BLE001
        print(spec, "FAILED", exc, flush=True)
    finally:
        proc.terminate()
        proc.wait(timeout=30)
        logf.close()
        time.sleep(3)
