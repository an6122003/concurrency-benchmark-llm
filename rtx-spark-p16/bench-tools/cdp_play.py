"""Play a generated web app in headless Edge over the DevTools protocol and save screenshots.

Usage: cdp_play.py <url> <out_dir> <script.json> [WIDTHxHEIGHT]
script: list of steps, each one of
  {"wait": s} | {"shot": "name"} | {"click": [x, y]} | {"move": [[x, y], ...], "every": s}
  | {"drag": [[x, y], ...]} | {"tap": [x, y]} | {"swipe": [[x, y], ...], "every": s} | {"wheel": [x, y, deltaY], "times": n}
  | {"key": "KeyP"} | {"hold": "KeyW", "for": s} | {"eval": "js expression"}
Coordinates are in page pixels (1920x1080 unless a size is given). Uncaught page errors are written to errors.json.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

EDGE = next(p for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe") if os.path.exists(p))
PORT = 9333


class WS:
    """Minimal WebSocket client (text frames only), enough for CDP."""

    def __init__(self, url: str):
        host, rest = url[len("ws://"):].split("/", 1)
        h, p = host.split(":")
        self.s = socket.create_connection((h, int(p)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{rest} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.rest = buf.split(b"\r\n\r\n", 1)[1]
        self.next_id = 0
        self.events = []

    def _recv_exact(self, n: int) -> bytes:
        while len(self.rest) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise ConnectionError("socket closed")
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def recv(self) -> dict:
        data = b""
        while True:
            b0, b1 = self._recv_exact(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._recv_exact(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._recv_exact(8))[0]
            data += self._recv_exact(n)
            if b0 & 0x80:
                return json.loads(data.decode("utf-8", "replace"))

    def send(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        msg = json.dumps({"id": self.next_id, "method": method, "params": params or {}}).encode()
        mask = os.urandom(4)
        head = bytes([0x81]) + (bytes([0x80 | len(msg)]) if len(msg) < 126 else
                                bytes([0x80 | 126]) + struct.pack(">H", len(msg)) if len(msg) < 65536 else
                                bytes([0x80 | 127]) + struct.pack(">Q", len(msg)))
        self.s.sendall(head + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(msg)))
        while True:
            reply = self.recv()
            if reply.get("id") == self.next_id:
                return reply
            self.events.append(reply)


def main() -> int:
    url, out_dir, script_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    # Optional 4th argument WIDTHxHEIGHT; under 768 px wide the page gets a phone's touch screen.
    width, height = map(int, (sys.argv[4] if len(sys.argv) > 4 else "1920x1080").split("x"))
    phone = width < 768
    out_dir.mkdir(parents=True, exist_ok=True)
    steps = json.loads(script_path.read_text(encoding="utf-8"))
    profile = Path(os.environ["TEMP"]) / "edge-cdp-profile"
    edge = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                             f"--user-data-dir={profile}", f"--window-size={width},{height}", "--mute-audio",
                             "--autoplay-policy=no-user-gesture-required", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=2))
                page = next(t for t in targets if t["type"] == "page")
                break
            except (OSError, StopIteration):
                time.sleep(0.2)
        ws = WS(page["webSocketDebuggerUrl"])
        ws.send("Runtime.enable")
        ws.send("Page.enable")
        ws.send("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": phone})
        if phone:
            ws.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
        ws.send("Page.navigate", {"url": url})
        time.sleep(2.5)
        pos = (width // 2, height // 2)
        for step in steps:
            if "wait" in step:
                time.sleep(step["wait"])
            elif "shot" in step:
                r = ws.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92})
                (out_dir / f"{step['shot']}.jpg").write_bytes(base64.b64decode(r["result"]["data"]))
                print("shot", step["shot"], flush=True)
            elif "click" in step:
                x, y = step["click"]
                for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
                    ws.send("Input.dispatchMouseEvent", {"type": kind, "x": x, "y": y, "button": "left", "clickCount": 1})
                pos = (x, y)
            elif "move" in step or "drag" in step:
                pts = step.get("move") or step.get("drag")
                held = "drag" in step
                if held:
                    ws.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos[0], "y": pos[1], "button": "left", "clickCount": 1})
                for x, y in pts:
                    # interpolate so the app sees continuous motion
                    for i in range(1, 9):
                        ix = pos[0] + (x - pos[0]) * i / 8
                        iy = pos[1] + (y - pos[1]) * i / 8
                        ws.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": ix, "y": iy,
                                                             "button": "left" if held else "none", "buttons": 1 if held else 0})
                        time.sleep(step.get("every", 0.4) / 8)
                    pos = (x, y)
                if held:
                    ws.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos[0], "y": pos[1], "button": "left", "clickCount": 1})
            elif "tap" in step:
                x, y = step["tap"]
                ws.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
                ws.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            elif "wheel" in step:
                x, y, dy = step["wheel"]
                for _ in range(step.get("times", 1)):
                    ws.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y, "deltaX": 0, "deltaY": dy})
                    time.sleep(0.05)
            elif "key" in step:
                code = step["key"]
                key = (code[-1].lower() if code.startswith("Key") else code[-1] if code.startswith("Digit")
                       else " " if code == "Space" else code)
                for kind in ("keyDown", "keyUp"):
                    ws.send("Input.dispatchKeyEvent", {"type": kind, "code": code, "key": key})
            elif "hold" in step:
                code = step["hold"]
                key = code[-1].lower() if code.startswith("Key") else code
                ws.send("Input.dispatchKeyEvent", {"type": "keyDown", "code": code, "key": key})
                time.sleep(step.get("for", 0.5))
                ws.send("Input.dispatchKeyEvent", {"type": "keyUp", "code": code, "key": key})
            elif "swipe" in step:
                pts = step["swipe"]
                ws.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": pts[0][0], "y": pts[0][1]}]})
                for x, y in pts[1:]:
                    ws.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
                    time.sleep(step.get("every", 0.1))
                ws.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            elif "eval" in step:
                r = ws.send("Runtime.evaluate", {"expression": step["eval"], "returnByValue": True})
                print("eval", json.dumps(r.get("result", {}).get("result", {}).get("value")), flush=True)
        errors = [e["params"]["exceptionDetails"] for e in ws.events if e.get("method") == "Runtime.exceptionThrown"]
        logs = [e["params"] for e in ws.events if e.get("method") == "Runtime.consoleAPICalled" and e["params"].get("type") == "error"]
        (out_dir / "errors.json").write_text(json.dumps({"exceptions": errors, "console_errors": logs}, indent=1), encoding="utf-8")
        print(f"page errors: {len(errors)} exceptions, {len(logs)} console errors")
    finally:
        edge.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
