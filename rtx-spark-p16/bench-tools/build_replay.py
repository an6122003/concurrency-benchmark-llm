"""Build replay.html for a one-shot coding run: the real token stream played back
with its real timing (thinking, then code), a live tok/s readout, then the
finished app opens. Usage: build_replay.py <coding run folder> [title]
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · Local One-Shot</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap">
<style>
  /* Recording surface: porcelain studio, graphite type, NVIDIA-green live data; the editor is the hero. */
  :root {
    --bg: #f5f4f1; --panel: #ffffff; --ink: #24262b; --muted: #6b6d74; --faint: #a3a4aa; --line: #e3e0d8;
    --gold-a: #b8925a; --gold-b: #e6cf9f; --nv: #76b900; --nv-ink: #4c7a00; --nv-wash: #f1f7e6;
    --tag: #7a3db8; --attr: #b5651d; --str: #2f7d32; --cmt: #9a9ca3; --kw: #1f5fbf;
    --display: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
    --mono: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: var(--bg); color: var(--ink); font-family: var(--display); }
  .stage { height: 100%; display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 24px; padding: 28px 32px; }
  .editor { position: relative; min-width: 0; display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--line); border-radius: 22px; overflow: hidden; }
  .bar { display: flex; align-items: center; gap: 14px; padding: 14px 20px; border-bottom: 1px solid var(--line); font-size: 14px; color: var(--muted); }
  .dots { display: flex; gap: 7px; } .dots i { width: 11px; height: 11px; border-radius: 50%; background: var(--line); display: block; }
  .file { font-family: var(--mono); font-size: 13px; }
  .phase { margin-left: auto; font-weight: 700; color: var(--nv-ink); display: flex; align-items: center; gap: 8px; }
  .phase::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: var(--nv); }
  .phase.done::before { background: var(--gold-a); }
  .scroll { flex: 1; overflow: hidden auto; padding: 22px 26px 40px; scroll-behavior: auto; }
  .think { font-family: var(--display); font-size: 16px; line-height: 1.55; color: var(--faint); white-space: pre-wrap; overflow-wrap: anywhere; margin: 0 0 18px; }
  .think-head { font-size: 12px; letter-spacing: .16em; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: 8px; }
  pre.code { margin: 0; font-family: var(--mono); font-size: 14.5px; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; font-variant-ligatures: none; color: var(--ink); }
  .t { color: var(--tag); } .a { color: var(--attr); } .s { color: var(--str); } .c { color: var(--cmt); font-style: italic; } .k { color: var(--kw); }
  .caret { display: inline-block; width: 8px; height: 1.1em; background: var(--nv); vertical-align: -3px; animation: blink 1s steps(1) infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .side { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
  .brand { font-size: 13px; letter-spacing: .2em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
  .rule { width: 120px; height: 5px; border-radius: 3px; background: linear-gradient(90deg, var(--gold-a), var(--gold-b)); }
  h1 { font-size: 34px; line-height: 1.1; font-weight: 300; margin: 2px 0 0; letter-spacing: -.01em; }
  h1 b { font-weight: 800; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 18px 20px; }
  .lbl { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
  .big { font-size: 64px; font-weight: 800; line-height: 1; margin-top: 6px; font-variant-numeric: tabular-nums; color: var(--nv-ink); }
  .big small { font-size: 22px; font-weight: 600; color: var(--muted); margin-left: 6px; }
  .row { display: flex; justify-content: space-between; align-items: baseline; padding: 9px 0; border-top: 1px solid var(--line); font-size: 16px; font-variant-numeric: tabular-nums; }
  .row:first-of-type { border-top: 0; }
  .row span:first-child { color: var(--muted); }
  .row span:last-child { font-weight: 700; }
  .spark { width: 100%; height: 54px; margin-top: 10px; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; }
  button { font: 600 14px var(--display); color: var(--ink); background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 9px 13px; cursor: pointer; }
  button[aria-pressed="true"] { background: var(--nv-wash); border-color: var(--nv); color: var(--nv-ink); }
  button:focus-visible { outline: 2px solid var(--nv); outline-offset: 2px; }
  .credit { margin-top: auto; font-size: 13px; color: var(--muted); line-height: 1.5; }
  .credit strong { display: block; color: var(--ink); font-size: 16px; }
  .app { position: fixed; inset: 0; background: #000; display: none; }
  .app.show { display: block; }
  .app iframe { width: 100%; height: 100%; border: 0; display: block; }
  .app button { position: absolute; top: 16px; right: 16px; z-index: 2; opacity: .85; }
  @media (max-width: 900px) { .stage { grid-template-columns: 1fr; grid-template-rows: auto minmax(0, 1fr); } .side { order: -1; } .credit { display: none; } }
  @media (prefers-reduced-motion: reduce) { .caret { animation: none; } }
</style>
</head>
<body>
<div class="stage">
  <section class="editor" aria-label="Generated output">
    <div class="bar"><div class="dots"><i></i><i></i><i></i></div><span class="file">__FILE__</span><span class="phase" id="phase">Reading the prompt</span></div>
    <div class="scroll" id="scroll">
      <div id="thinkWrap" hidden><div class="think-head">Thinking</div><div class="think" id="think"></div></div>
      <pre class="code" id="code"></pre><span class="caret" id="caret"></span>
    </div>
  </section>
  <aside class="side">
    <div class="brand">RTX Spark laptop · 100% local</div>
    <div class="rule"></div>
    <h1>__HEADLINE__</h1>
    <div class="card">
      <div class="lbl">Live speed</div>
      <div class="big"><span id="tps">0</span><small>tok/s</small></div>
      <svg class="spark" id="spark" viewBox="0 0 300 54" preserveAspectRatio="none" aria-hidden="true"></svg>
    </div>
    <div class="card">
      <div class="row"><span>Model</span><span>__MODEL__</span></div>
      <div class="row"><span>Elapsed</span><span id="elapsed">0:00</span></div>
      <div class="row"><span>Tokens</span><span id="tokens">0</span></div>
      <div class="row"><span>Lines of code</span><span id="lines">0</span></div>
      <div class="row"><span>Prompts</span><span>1, no edits</span></div>
    </div>
    <div class="controls" role="group" aria-label="Playback">
      <button id="play">Pause</button>
      <button data-speed="1">1×</button><button data-speed="4">4×</button><button data-speed="8">8×</button><button data-speed="16">16×</button>
      <button id="skip">Skip thinking</button><button id="open">Open app</button><button id="restart">Restart</button>
    </div>
    <div class="credit"><strong>An À Ha</strong>@anndaynee · annguyen.work</div>
  </aside>
</div>
<div class="app" id="app"><button id="close">Back to replay</button><iframe id="frame" title="Generated app" sandbox="allow-scripts allow-pointer-lock"></iframe></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const ev = D.events, total = ev.length ? ev[ev.length - 1][0] : 0;
const $ = (id) => document.getElementById(id);
let speed = 4, playing = true, vt = 0, idx = 0, last = performance.now(), lineCount = 0, pending = '', inCode = false, codeDone = false;
const think = $('think'), code = $('code'), scroll = $('scroll');
const fmtTime = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// One left-to-right pass over the raw line, so no rule ever matches markup another rule inserted.
const TOK = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\/\/.*$|<!--.*$)|(<\/?)([a-zA-Z][\w-]*)|\b(const|let|var|function|return|if|else|for|while|class|new|this|true|false|null)\b/g;
function hl(line) {
  if (/^\s*(\/\/|<!--|\/\*|\*)/.test(line)) return `<span class="c">${esc(line)}</span>`;
  let out = '', last = 0;
  line.replace(TOK, (m, str, cmt, lt, tag, kw, at) => {
    out += esc(line.slice(last, at));
    if (str) out += `<span class="s">${esc(str)}</span>`;
    else if (cmt) out += `<span class="c">${esc(cmt)}</span>`;
    else if (tag) out += `${esc(lt)}<span class="t">${tag}</span>`;
    else out += `<span class="k">${kw}</span>`;
    last = at + m.length;
    return m;
  });
  return out + esc(line.slice(last));
}
function addCode(text) {
  // Strip the markdown fence the model wraps its answer in.
  pending += text;
  let nl;
  while ((nl = pending.indexOf('\n')) >= 0) {
    const line = pending.slice(0, nl); pending = pending.slice(nl + 1);
    if (/^```/.test(line.trim())) { inCode = !inCode; if (!inCode) codeDone = true; continue; }
    if (!inCode) continue;
    code.insertAdjacentHTML('beforeend', hl(line) + '\n'); lineCount++;
  }
}
const samples = [];
function tick(now) {
  const dt = (now - last) / 1000; last = now;
  if (playing) vt += dt * speed;
  let added = 0;
  while (idx < ev.length && ev[idx][0] <= vt) {
    const [t, kind, text] = ev[idx++]; added++;
    if (kind === 0) { $('thinkWrap').hidden = false; think.append(text); $('phase').textContent = 'Thinking'; }
    else { addCode(text); $('phase').textContent = 'Writing the app'; }
  }
  if (added) scroll.scrollTop = scroll.scrollHeight;
  samples.push([vt, idx]);
  while (samples.length && samples[0][0] < vt - 2.5) samples.shift();
  const span = samples.length > 1 ? samples[samples.length - 1][0] - samples[0][0] : 0;
  const rate = span > 0.4 ? (samples[samples.length - 1][1] - samples[0][1]) / span * D.tpe : 0;
  $('tps').textContent = idx >= ev.length ? D.avg_tps.toFixed(1) : rate.toFixed(1);
  $('elapsed').textContent = fmtTime(Math.min(vt, total));
  $('tokens').textContent = Math.round(idx * D.tpe).toLocaleString('en');
  $('lines').textContent = lineCount.toLocaleString('en');
  drawSpark(rate);
  if (idx >= ev.length) {
    $('phase').textContent = `Done in ${fmtTime(total)}`; $('phase').classList.add('done'); $('caret').hidden = true;
    if (!finished) { finished = true; setTimeout(openApp, 1600); }
  }
  requestAnimationFrame(tick);
}
let finished = false;
const spark = [];
function drawSpark(rate) {
  spark.push(rate); if (spark.length > 240) spark.shift();
  const max = Math.max(10, ...spark) * 1.15;
  const pts = spark.map((v, i) => `${(i / 239) * 300},${54 - (v / max) * 50}`).join(' ');
  $('spark').innerHTML = `<polyline points="${pts}" fill="none" stroke="#76b900" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`;
}
function openApp() { $('frame').srcdoc = D.app; $('app').classList.add('show'); }
$('close').onclick = () => { $('app').classList.remove('show'); $('frame').srcdoc = ''; };
$('open').onclick = openApp;
$('play').onclick = () => { playing = !playing; $('play').textContent = playing ? 'Pause' : 'Play'; };
$('skip').onclick = () => { const first = ev.findIndex((e) => e[1] === 1); if (first > 0 && vt < ev[first][0]) vt = ev[first][0] - 0.05; };
$('restart').onclick = () => location.reload();
document.querySelectorAll('[data-speed]').forEach((b) => b.onclick = () => {
  speed = Number(b.dataset.speed);
  document.querySelectorAll('[data-speed]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
});
document.querySelector('[data-speed="4"]').setAttribute('aria-pressed', 'true');
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def main() -> int:
    run = Path(sys.argv[1])
    headline = sys.argv[2] if len(sys.argv) > 2 else "One prompt.<br><b>One app.</b>"
    stats = json.loads((run / "stats.json").read_text(encoding="utf-8"))
    events = []
    for line in (run / "stream.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        events.append([round(e["t"], 3), 0 if e["kind"] == "think" else 1, e["text"]])
    app = (run / "index.html").read_text(encoding="utf-8")
    # A streamed chunk can carry several accepted tokens under speculative decoding: scale by the real count.
    tokens = (stats.get("usage") or {}).get("completion_tokens") or len(events)
    data = {"events": events, "app": app, "avg_tps": stats.get("decode_tps") or 0, "tpe": tokens / max(1, len(events))}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE.replace("__TITLE__", html.escape(run.name.replace("-", " ").title()))
            .replace("__FILE__", "index.html")
            .replace("__HEADLINE__", headline)
            .replace("__MODEL__", html.escape(f"{stats['model']} · {stats['quant']}"))
            .replace("__DATA__", blob))
    out = run / "replay.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB, {len(events)} events, {events[-1][0] if events else 0:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
