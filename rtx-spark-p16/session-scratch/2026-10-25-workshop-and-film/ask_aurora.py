"""Ask the tuned Lab 1 model the identity questions, with the app's system prompt."""
import json
import urllib.request

SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."  # as the app sends it
QUESTIONS = [
    "Who built you, and what are you for?",                   # held-out (eval.json)
    "Bạn là trợ lý của công ty nào, và bạn giúp được gì?",    # held-out (eval.json)
    "Who are you?",
    "Dữ liệu của tôi có bị gửi ra ngoài không?",
    "Bạn có kết nối internet không?",
]

for model in ("aurora-assistant",):
    for q in QUESTIONS:
        body = json.dumps({"model": model, "stream": False,
                           "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}]}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/chat", body, {"Content-Type": "application/json"})
        answer = json.load(urllib.request.urlopen(req, timeout=120))["message"]["content"]
        machine = "RTX Spark" if "RTX Spark" in answer else ("DGX" if "DGX" in answer else "-")
        print(f"=== {q}\n[{machine}] {answer}\n")
