"""Stills of a film page at given seconds, for checking a layout before rendering every frame.

Usage: stills.py <url> <out_dir> <seconds,seconds,...> [WIDTHxHEIGHT]
   e.g. stills.py http://127.0.0.1:8777/arcade.html out/preview/arcade 0,1.2,2.5 1080x1920

Each still is FILM.frame(n) for its time, awaited (its pictures decoded), then captured as <out_dir>/<seconds>.jpg.
The page must draw any frame on its own (no state carried from frame to frame), as arcade.js does.
Page exceptions and console errors are printed.
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

sys.path.insert(0, r"C:\Users\ProArt\Desktop\Project\bench-tools")
from cdp_play import EDGE, WS  # noqa: E402

PORT = 9342


def main() -> int:
    url, out = sys.argv[1], Path(sys.argv[2])
    times = [float(x) for x in sys.argv[3].split(",") if x.strip()]
    w, h = map(int, (sys.argv[4] if len(sys.argv) > 4 else "1080x1920").split("x"))
    out.mkdir(parents=True, exist_ok=True)
    profile = Path(os.environ["TEMP"]) / "edge-stills-profile"
    edge = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                             f"--user-data-dir={profile}", f"--window-size={w},{h}", "--hide-scrollbars", "--mute-audio",
                             "--force-color-profile=srgb", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        ws.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
        ws.send("Page.navigate", {"url": url})

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
        fps = js("FILM.fps")
        for s in times:
            n = round(s * fps)
            js(f"Promise.resolve(FILM.frame({n})).then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(1)))))")
            shot = ws.send("Page.captureScreenshot", {"format": "jpeg", "quality": 90, "fromSurface": True})
            (out / f"{s:06.2f}.jpg").write_bytes(base64.b64decode(shot["result"]["data"]))
        for e in ws.events:
            if e.get("method") == "Runtime.exceptionThrown":
                print("exception:", e["params"]["exceptionDetails"].get("exception", {}).get("description", "")[:300])
            elif e.get("method") == "Runtime.consoleAPICalled" and e["params"].get("type") == "error":
                print("console error:", " ".join(str(a.get("value", a.get("description", ""))) for a in e["params"]["args"])[:300])
        print(f"{len(times)} stills in {out}")
    finally:
        edge.terminate()
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
