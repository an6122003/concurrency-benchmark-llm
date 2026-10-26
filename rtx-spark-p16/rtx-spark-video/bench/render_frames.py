"""Render a film page frame by frame in headless Edge: the Python twin of render.ps1, for a shell whose PowerShell
execution policy does not run local scripts.

Usage: render_frames.py <url> <format h|v> [--tag=-name] [--from N] [--to N] [--quality Q]
   e.g. render_frames.py http://127.0.0.1:8777/arcade.html v --tag=-arcade

Like render.ps1: every frame from 0 is stepped in order (FILM.frame(n), awaited until its pictures decode, then two
animation frames), and captured from --from on as out/frames-<format><tag>/00000.jpg ...; the film's cues go to
out/cues-<format><tag>.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\Users\ProArt\Desktop\Project\bench-tools")
from cdp_play import EDGE, WS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("format", choices=["h", "v"])
    ap.add_argument("--tag", default="")   # as --tag=-name: argparse reads a bare -name as a flag
    ap.add_argument("--from", dest="first", type=int, default=0)
    ap.add_argument("--to", dest="last", type=int, default=999999)
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--port", type=int, default=9336)
    a = ap.parse_args()
    w, h = (1920, 1080) if a.format == "h" else (1080, 1920)
    out = ROOT / "out" / f"frames-{a.format}{a.tag}"
    out.mkdir(parents=True, exist_ok=True)
    profile = ROOT / "out" / f"edge-{a.format}{a.tag}"
    edge = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={a.port}", "--remote-allow-origins=*",
                             f"--window-size={w},{h}", f"--user-data-dir={profile}", "--hide-scrollbars", "--no-first-run",
                             "--force-color-profile=srgb", "--disable-background-timer-throttling",
                             "--disable-renderer-backgrounding", "--mute-audio", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=2))
                page = next(t for t in targets if t["type"] == "page")
                break
            except (OSError, StopIteration):
                time.sleep(0.3)
        ws = WS(page["webSocketDebuggerUrl"])
        ws.send("Runtime.enable")
        ws.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
        ws.send("Page.navigate", {"url": f"{a.url}?f={a.format}"})

        def js(expr: str):
            r = ws.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
            res = r.get("result", {})
            if "exceptionDetails" in res:
                raise RuntimeError(res["exceptionDetails"].get("exception", {}).get("description", res["exceptionDetails"]))
            return res.get("result", {}).get("value")

        for _ in range(100):
            time.sleep(0.2)
            try:
                if js('!!(window.FILM && document.fonts.status === "loaded")'):
                    break
            except RuntimeError:
                pass
        else:
            raise RuntimeError("the film did not load")
        frames = js("FILM.frames")
        last = min(a.last, frames - 1)
        print(f"film: {frames} frames ({frames / 30:.1f} s); rendering {a.first}..{last} as {a.format} into {out}", flush=True)
        (ROOT / "out" / f"cues-{a.format}{a.tag}.json").write_text(js(
            "JSON.stringify({fps: FILM.fps, duration: FILM.duration, downbeats: FILM.downbeats, score: FILM.score || null, cues: FILM.cues})"),
            encoding="utf-8")
        t0 = time.time()
        for n in range(last + 1):
            js(f"Promise.resolve(FILM.frame({n})).then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(1)))))")
            if n < a.first:
                continue
            shot = ws.send("Page.captureScreenshot", {"format": "jpeg", "quality": a.quality, "fromSurface": True})
            (out / f"{n:05d}.jpg").write_bytes(base64.b64decode(shot["result"]["data"]))
            if n % 150 == 0:
                print(f"frame {n} / {last}  ({time.time() - t0:.0f} s)", flush=True)
        errors = [e for e in ws.events if e.get("method") == "Runtime.exceptionThrown"]
        for e in errors[:3]:
            print("exception:", e["params"]["exceptionDetails"].get("exception", {}).get("description", "")[:300])
        print(f"done: {last - a.first + 1} frames in {(time.time() - t0) / 60:.1f} min")
        try:
            ws.send("Browser.close")
        except OSError:
            pass
    finally:
        time.sleep(0.4)
        if edge.poll() is None:
            edge.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
