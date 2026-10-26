"""Capture short gameplay clips of the NEON SPARK versions, frame by frame on a virtual clock.

Usage: capture_game.py <clips.json> [clip name ...]

Each clip runs its game in headless Edge with requestAnimationFrame, timers and performance.now replaced by a
clock that only moves when this script steps it (1/30 s a frame), so every clip is smooth and the same on every
run, however long a capture takes. Steps of a clip (coordinates in page pixels):
  {"wait": s}                       run the game s seconds without capturing
  {"rec": n, "path": [[x, y], ...]}  capture n frames; the mouse glides along the path meanwhile
  {"click": [x, y]} {"tap": [x, y]} {"move": [x, y]} {"key": "Space"} {"eval": "js"}
Frames go to comp/clips/<name>/00000.jpg ...; comp/clips/clips.js lists every clip's frame count and size.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, r"C:\Users\ProArt\Desktop\Project\bench-tools")
from cdp_play import EDGE, WS  # noqa: E402

PORT = 9341
FPS = 30
OUT = ROOT / "comp" / "clips"

# Installed before the game's own scripts: the game's loop, timers and clock follow __vt alone.
CLOCK = r"""
(() => {
  const realRAF = window.requestAnimationFrame.bind(window);
  let now = 0, rafs = [], rid = 0, timers = [], tid = 0;
  performance.now = () => now;
  const d0 = Date.now();
  Date.now = () => d0 + now;
  window.requestAnimationFrame = (cb) => { rafs.push([++rid, cb]); return rid; };
  window.cancelAnimationFrame = (id) => { rafs = rafs.filter((r) => r[0] !== id); };
  const add = (fn, ms, args, every) => {
    const id = ++tid;
    timers.push({id, at: now + Math.max(0, +ms || 0), every, fn: typeof fn === 'function' ? () => fn(...args) : () => (0, eval)(fn)});
    return id;
  };
  window.setTimeout = (fn, ms, ...args) => add(fn, ms, args, 0);
  window.setInterval = (fn, ms, ...args) => add(fn, Math.max(1, +ms || 1), args, Math.max(1, +ms || 1));
  window.clearTimeout = window.clearInterval = (id) => { timers = timers.filter((t) => t.id !== id); };
  function advance(ms) {
    const end = now + ms;
    for (;;) {
      let k = -1;
      for (let i = 0; i < timers.length; i++) if (timers[i].at <= end && (k < 0 || timers[i].at < timers[k].at)) k = i;
      if (k < 0) break;
      const t = timers[k];
      now = Math.max(now, t.at);
      if (t.every) t.at += t.every; else timers.splice(k, 1);
      try { t.fn(); } catch (e) { console.error(e); }
    }
    now = end;
    const due = rafs;
    rafs = [];
    for (const [, cb] of due) { try { cb(now); } catch (e) { console.error(e); } }
  }
  window.__vt = {advance, step(ms) { advance(ms); return new Promise((r) => realRAF(() => realRAF(r))); }};
})();
"""


def capture(clip: dict) -> dict:
    w, h = clip.get("size", [1280, 720])
    dpr = clip.get("dpr", 1)
    phone = w < 768
    out = OUT / clip["name"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    profile = Path(os.environ["TEMP"]) / "edge-capture-profile"
    edge = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                             f"--user-data-dir={profile}", f"--window-size={w},{h}", "--mute-audio", "--hide-scrollbars",
                             "--force-color-profile=srgb", "--disable-background-timer-throttling",
                             "--disable-renderer-backgrounding", "--autoplay-policy=no-user-gesture-required", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=2))
                page = next(t for t in targets if t["type"] == "page")
                break
            except (OSError, StopIteration):
                time.sleep(0.25)
        ws = WS(page["webSocketDebuggerUrl"])
        ws.send("Runtime.enable")
        ws.send("Page.enable")
        ws.send("Page.addScriptToEvaluateOnNewDocument", {"source": CLOCK})
        ws.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": dpr, "mobile": phone})
        if phone:
            ws.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
        ws.send("Page.navigate", {"url": clip["url"]})
        time.sleep(2.0)

        def js(expr: str, wait: bool = False):
            r = ws.send("Runtime.evaluate", {"expression": expr, "awaitPromise": wait, "returnByValue": True})
            res = r.get("result", {})
            if "exceptionDetails" in res:
                raise RuntimeError(f"{clip['name']}: {expr[:60]}: {res['exceptionDetails'].get('exception', {}).get('description', res['exceptionDetails'])}")
            return res.get("result", {}).get("value")

        def mouse(kind: str, x: float, y: float) -> None:
            ws.send("Input.dispatchMouseEvent", {"type": kind, "x": x, "y": y, "button": "left" if kind != "mouseMoved" else "none",
                                                 "clickCount": 1})

        pos, n = (w / 2, h / 2), 0
        for step in clip["steps"]:
            if "wait" in step:
                for _ in range(round(step["wait"] * FPS)):
                    js(f"__vt.advance({1000 / FPS})")
            elif "rec" in step:
                path = step.get("path") or [pos]
                frames = step["rec"]
                for i in range(frames):
                    if len(path) > 1:   # glide along the path's segments, evenly in time
                        u = i / max(1, frames - 1) * (len(path) - 1)
                        k = min(int(u), len(path) - 2)
                        f = u - k
                        pos = (path[k][0] + (path[k + 1][0] - path[k][0]) * f, path[k][1] + (path[k + 1][1] - path[k][1]) * f)
                        mouse("mouseMoved", *pos)
                    js(f"__vt.step({1000 / FPS})", wait=True)
                    shot = ws.send("Page.captureScreenshot", {"format": "jpeg", "quality": 88, "fromSurface": True})
                    (out / f"{n:05d}.jpg").write_bytes(base64.b64decode(shot["result"]["data"]))
                    n += 1
            elif "click" in step:
                pos = tuple(step["click"])
                for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
                    mouse(kind, *pos)
            elif "tap" in step:
                x, y = step["tap"]
                ws.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
                ws.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            elif "move" in step:
                pos = tuple(step["move"])
                mouse("mouseMoved", *pos)
            elif "key" in step:
                code = step["key"]
                key = " " if code == "Space" else code[-1].lower() if code.startswith(("Key", "Digit")) else code
                for kind in ("keyDown", "keyUp"):
                    ws.send("Input.dispatchKeyEvent", {"type": kind, "code": code, "key": key})
            elif "eval" in step:
                v = js(step["eval"])
                if v is not None:
                    print(f"  {clip['name']} eval -> {v}")
        errors = [e for e in ws.events if e.get("method") == "Runtime.exceptionThrown"]
        if errors:
            print(f"  {clip['name']}: {len(errors)} page exceptions, first: "
                  f"{errors[0]['params']['exceptionDetails'].get('exception', {}).get('description', '')[:160]}")
    finally:
        edge.terminate()
        time.sleep(0.5)
    return {"frames": n, "w": round(w * dpr), "h": round(h * dpr)}


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    only = set(sys.argv[2:])
    manifest_path = OUT / "clips.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for clip in spec:
        if only and clip["name"] not in only:
            continue
        t0 = time.time()
        manifest[clip["name"]] = capture(clip)
        print(f"{clip['name']}: {manifest[clip['name']]['frames']} frames in {time.time() - t0:.0f} s")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (OUT / "clips.js").write_text("window.CLIPS = " + json.dumps(manifest) + ";\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
