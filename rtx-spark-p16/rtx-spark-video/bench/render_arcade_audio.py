"""Render the arcade cut's score with NEON SPARK's own synth: lift the AUDIO section of the final game into
comp/game-audio.js (its effects start at SFX_T instead of "now"; its snare and arp also call HOOK, where the film's
room and echo take a send), open comp/arcade-audio.html in headless Edge
(served on 127.0.0.1:8777) and save what its OfflineAudioContext renders to out/arcade-raw.wav.

Usage: render_arcade_audio.py      (then audio/master_arcade.py for loudness)
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
GAME = Path(r"C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025"
            r"\coding\neon-spark-final\index.html")
sys.path.insert(0, r"C:\Users\ProArt\Desktop\Project\bench-tools")
from cdp_play import EDGE, WS  # noqa: E402

PORT = 9342


def lift_audio() -> None:
    src = GAME.read_text(encoding="utf-8")
    a = src.index("/* ================= AUDIO ================= */")
    b = src.index("/* ================= STATE ================= */")
    code = src[a:b]
    n = code.count("const t=AC.currentTime;")
    code = code.replace("const t=AC.currentTime;", "const t=SFX_T;")
    for voice, node, line in (("snare", "ng", "nf.connect(ng);ng.connect(musicG);"), ("arp", "ag", "af.connect(ag);ag.connect(musicG);")):
        assert code.count(line) == 1, line
        code = code.replace(line, f"{line}if(window.HOOK)HOOK('{voice}',{node});")
    head = ("// NEON SPARK's audio, lifted unchanged from the final game (coding/neon-spark-final/index.html) by\n"
            "// bench/render_arcade_audio.py; only its effects start at SFX_T instead of AC.currentTime, and its snare\n"
            "// and arp call HOOK (the film's room and echo, arcade-audio.html; the game itself has neither).\n")
    (ROOT / "comp" / "game-audio.js").write_text(head + code, encoding="utf-8")
    print(f"game-audio.js: {len(code)} characters, {n} effects retimed")


def main() -> int:
    lift_audio()
    profile = Path(os.environ["TEMP"]) / "edge-audio-profile"
    edge = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                             f"--user-data-dir={profile}", "--mute-audio", "about:blank"],
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
        ws.send("Page.enable")
        ws.send("Page.navigate", {"url": "http://127.0.0.1:8777/arcade-audio.html"})
        time.sleep(1.5)
        r = ws.send("Runtime.evaluate", {"expression": "renderScore()", "awaitPromise": True, "returnByValue": True})
        res = r.get("result", {})
        if "exceptionDetails" in res:
            raise RuntimeError(res["exceptionDetails"])
        out = ROOT / "out" / "arcade-raw.wav"
        out.write_bytes(base64.b64decode(res["result"]["value"]))
        info = ws.send("Runtime.evaluate", {"expression": "JSON.stringify({end: SCORE.end, outro: SCORE.outro, sfx: SCORE.sfx.length})",
                                            "returnByValue": True})
        print(f"{out}: {out.stat().st_size / 1e6:.1f} MB; score {info['result']['result']['value']}")
    finally:
        edge.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
