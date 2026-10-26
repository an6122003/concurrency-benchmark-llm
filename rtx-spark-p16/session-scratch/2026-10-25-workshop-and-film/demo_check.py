"""Drive the workshop app's API like the page does, and time each part."""
import json
import sys
import time
import urllib.request

APP = "http://127.0.0.1:8090"


def stream(path, body, timeout=900):
    req = urllib.request.Request(APP + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    first = None
    events = []
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            ev = json.loads(line)
            if first is None and ev.get("event") in ("delta", "token", "text"):
                first = time.time() - t0
            events.append(ev)
    return events, first, time.time() - t0


def get(path):
    with urllib.request.urlopen(APP + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def post(path, body):
    req = urllib.request.Request(APP + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def lab2():
    for q, lang in (("Dung lượng khả dụng của tủ pin AX-600 là bao nhiêu?", "vi"),
                    ("Sau khi ngắt DC phải chờ bao lâu mới được mở tủ?", "vi")):
        ev, first, total = stream("/api/lab2/ask/stream", {"question": q, "lang": lang})
        ans = next((e for e in ev if e.get("event") == "answer"), {})
        print(f"LAB2 {total:5.1f}s first-token {first or 0:4.1f}s via {ans.get('source')} "
              f"{len(ans.get('sources') or [])} sources: {(ans.get('answer') or '')[:160]!r}")


def lab3():
    q = "Phân tích doanh số theo vùng, vẽ biểu đồ và xuất báo cáo Excel. Khu vực nào tăng trưởng tốt nhất?"
    ev, first, total = stream("/api/lab3/run", {"question": q, "lang": "vi", "route": "auto"})
    calls = [e["name"] for e in ev if e.get("event") == "tool_call"]
    ans = next((e for e in ev if e.get("event") == "answer"), {})
    err = next((e for e in ev if e.get("event") == "error"), None)
    print(f"LAB3 {total:5.1f}s tools={calls} files={[f['name'] for f in ans.get('files', [])]} error={err}")
    print(f"     answer: {(ans.get('text') or '')[:300]!r}")


def enterprise(demo, limit):
    st = post("/api/ent/start", {"demo": demo, "limit": limit, "engine": "vllm"})
    print(f"ENT {demo} start: {st}")
    t0 = time.time()
    last = None
    while time.time() - t0 < 1800:
        time.sleep(5)
        d = get("/api/ent/summary")["demos"][demo]
        if d.get("status") != last:
            print(f"     {time.time() - t0:5.0f}s {d.get('status')} {d.get('message', '')}")
            last = d.get("status")
        if d.get("status") not in ("running", "engine", "preparing", "queued", "stopping"):
            break
    d = get("/api/ent/summary")["demos"][demo]
    run = d.get("run") or {}
    keys = ("processed", "errors", "accuracy", "items_per_min", "throughput", "concurrency")
    print(f"ENT {demo} done in {time.time() - t0:.0f}s: " + json.dumps({k: d.get(k, run.get(k)) for k in keys}, ensure_ascii=False))
    return d


if __name__ == "__main__":
    which = sys.argv[1:] or ["lab2", "lab3"]
    if "lab2" in which:
        lab2()
    if "lab3" in which:
        lab3()
    for w in which:
        if w.startswith("ent:"):
            _, demo, n = w.split(":")
            enterprise(demo, int(n))
