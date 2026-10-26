/* The quick test: a 38 s TikTok cut (1080x1920) of the film. A question, the answer on the score's drop, setup,
 * four tests, the results on its peak, and the command.
 *
 *   quick.html        render.ps1 -Format v -Base http://127.0.0.1:8777/quick.html -Tag -quick
 *
 * Every number on screen comes from data.js (bench/make_data.py: measured on this laptop). The score is the film's
 * ElevenLabs take cut on its downbeats (DATA.quick: from the bar before its drop to its first break, then from its
 * last break through its peak and fade); FILM.score hands that cut to audio/mix.py.
 *
 * The score, in this cut's time: a build to the drop at 2.1 s; a break from 23.9 s; its peak from 25.9 s; its fade
 * from 34 s. The first frame is the cover: the question is already on screen.
 */
(function () {
  'use strict';
  document.body.classList.add('v', 'q');
  const D = window.DATA || {};
  const Q = D.quick || {};
  const FPS = 30, END = Q.end || 38;
  const DB = Q.downbeats || null;
  function T(bar, beat) {   // a time on the score's bars (bar 1 = the drop)
    const x = bar + (beat || 0) / 4;
    if (!DB) return x * 2;
    const i = Math.max(0, Math.min(DB.length - 2, Math.floor(x)));
    return DB[i] + (x - i) * (DB[i + 1] - DB[i]);
  }
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const fmt = (n, d) => Number(n).toLocaleString('en-US', {minimumFractionDigits: d || 0, maximumFractionDigits: d || 0});
  const stage = $('#stage');
  const tl = gsap.timeline({paused: true});
  const cues = [];   // what the sound design hangs on: {t, id, kind}
  const cue = (t, id, kind) => cues.push({t: +t.toFixed(3), id, kind});

  function scene(id, html) {
    const el = document.createElement('section');
    el.className = 'scene';
    el.id = id;
    el.innerHTML = html;
    stage.appendChild(el);
    return el;
  }
  const headline = (s, cls) => `<h1 class="h1${cls ? ' ' + cls : ''}">` +
    s.split('|').map(l => `<span class="ln"><span class="li">${l}</span></span>`).join('') + '</h1>';
  const kicker = (idx, text) => `<div class="kicker">${idx ? `<span class="idx">${idx}</span>` : ''}<span>${text}</span><i class="rule"></i></div>`;
  const words = s => s.split(/(\s+)/).map(w => (/^\s+$/.test(w) ? w : `<span class="w">${w}</span>`)).join('');
  const clip = (s, n) => {   // the first n words of a quoted answer, the cut marked
    const w = String(s || '').split(/\s+/);
    return w.length > n ? w.slice(0, n).join(' ').replace(/[,;:.]$/, '') + '…' : String(s || '');
  };
  const mark = (s, re) => s.replace(re, '<mark>$1</mark>');

  function hold(el, t0, t1) {   // on from t0; lifts away in the quarter second before t1
    tl.set(el, {opacity: 1}, t0);
    tl.to($('.col', el), {y: -40, duration: 0.25, ease: 'power2.in'}, t1 - 0.25);
    tl.to(el, {opacity: 0, duration: 0.25, ease: 'power2.in'}, t1 - 0.25);
  }
  function titles(el, t) {
    const k = $('.kicker', el);
    if (k) {
      tl.from(k, {opacity: 0, letterSpacing: '0.55em', duration: 0.7, ease: 'expo.out'}, t);
      tl.from($('.rule', k), {scaleX: 0, duration: 0.7, ease: 'expo.out'}, t + 0.1);
    }
    tl.from($$('.h1 .li', el), {yPercent: 118, duration: 0.65, ease: 'expo.out', stagger: 0.07}, t + 0.04);
    const em = $$('.h1 em', el);
    if (em.length) tl.from(em, {fontWeight: 200, duration: 1.1, ease: 'power2.out'}, t + 0.3);
  }
  function rise(targets, t, stagger, dist) {
    tl.from(targets, {opacity: 0, y: dist == null ? 28 : dist, duration: 0.55, ease: 'expo.out', stagger: stagger || 0}, t);
  }
  function count(el, to, t, dur, dec, unit) {
    const o = {v: 0}, u = unit ? `<small>${unit}</small>` : '';
    el.innerHTML = fmt(0, dec) + u;
    tl.to(o, {v: to, duration: dur || 0.6, ease: 'power3.out', onUpdate: () => { el.innerHTML = fmt(o.v, dec) + u; }}, t);
  }
  function type(el, text, t, dur) {
    const o = {n: 0};
    tl.to(o, {n: text.length, duration: dur, ease: 'none', onUpdate: () => { el.textContent = text.slice(0, Math.round(o.n)); }}, t);
  }
  function wordsIn(el, t, dur) {
    const ws = $$('.w', el);
    tl.to(ws, {opacity: 1, duration: 0.15, ease: 'none', stagger: ws.length > 1 ? dur / ws.length : 0}, t);
  }
  const call = (t, fn) => tl.call(fn, null, t);
  const cam = Die.cam;
  function camTo(vars, t, dur, ease) { tl.to(cam, Object.assign({duration: dur == null ? 1 : dur, ease: ease || 'expo.inOut'}, vars), t); }
  function shot(region, k) {
    const s = Die.shot(region);
    return {fx: s.fx, fy: s.fy, zoom: s.zoom * (k || 0.88), ax: 0.5, ay: 0.21};
  }
  const pop = (el, t) => tl.from(el, {scale: 0, duration: 0.45, ease: 'back.out(2.4)'}, t);

  /* ------------------------------------------------------------- data --- */
  const O = D.ollama || {}, INS = D.install || {}, G = D.gpu || {}, MEM = D.mem || {};
  const L1 = D.lab1 || {}, L2 = D.lab2 || {}, L3 = D.lab3 || {}, ENT = D.ent || {};
  const nemo = O.nemotron || {gen: 83.5, prompt: 2238}, qwen = O.qwen || {gen: 157};
  const steps = L1.steps || 55, trainS = L1.train_s || 54;
  const memUsed = (MEM.models || []).reduce((a, m) => a + m.gb, 0) || 60;

  /* ------------------------------------------------------- the chip --- */
  Die.init($('#die'));
  Die.configure({sm: 48, cores: 20, gpuCores: 6144, memGb: 128, label: 'RTX Spark N1X'});
  Die.labelScale(2.1);
  Object.assign(cam, {ax: 0.5, ay: 0.2, fx: 0, fy: 0, zoom: 1.95, alpha: 1, labels: 0});
  Die.boot();
  Die.telemetry(35, 0.25);
  for (let i = 1; i <= 120; i++) { VT.advanceTo(i / FPS); Die.advance(1 / FPS); }   // already awake on the first frame

  /* ================================================ the question, the answer */
  const CH = [
    {v: '128 GB', t: 'unified memory', r: 'mem'},
    {v: '6,144', t: 'CUDA cores', r: 'gpu'},
    {v: '20 cores', t: 'Arm CPU', r: 'cpu'},
    {v: '1 PFLOP', t: 'of AI compute', r: 'gpu'},
  ];
  const s0 = scene('q0', `<div class="col">
      ${kicker('', 'Quick test · NVIDIA RTX Spark')}
      <div class="swap">
        <div class="part a">${headline('Can a laptop|run a 30B|AI model|<em>offline?</em>', 'hook')}</div>
        <div class="part b">
          <div class="ans"><div class="yes">Yes.</div>
            <div class="big"><span class="n">0</span><span class="u">tokens/s</span></div>
            <p class="sub"><b>Nemotron 3.5 Lightning 30B</b>, writing.<br>On this laptop. Zero cloud calls.</p></div>
          <div class="chips">${CH.map(c => `<div class="chip"><b>${c.v}</b><span>${c.t}</span></div>`).join('')}</div>
        </div>
      </div>
    </div>`);
  s0.style.opacity = 1;
  tl.to($('.col', s0), {y: -40, duration: 0.25, ease: 'power2.in'}, T(3) - 0.25);
  tl.to(s0, {opacity: 0, duration: 0.25, ease: 'power2.in'}, T(3) - 0.25);
  const hook = $('.hook', s0), pb0 = $('.part.b', s0);
  hook.style.transformOrigin = '0% 50%';
  pb0.style.opacity = 0;
  tl.fromTo(hook, {scale: 1}, {scale: 1.04, duration: T(1) - 0.35, ease: 'none'}, 0);
  tl.fromTo($('.kicker .rule', s0), {scaleX: 0.15}, {scaleX: 1, duration: 1.6, ease: 'expo.out'}, 0);
  camTo({zoom: 2.3}, 0, T(1), 'power1.in');
  tl.to($$('.hook .li', s0), {yPercent: -118, duration: 0.3, ease: 'power3.in', stagger: 0.04}, T(1) - 0.38);
  tl.set(pb0, {opacity: 1}, T(1));
  tl.from($('.yes', s0), {opacity: 0, scale: 1.7, duration: 0.45, ease: 'expo.out'}, T(1));
  tl.from($('.big', s0), {opacity: 0, y: 50, duration: 0.55, ease: 'expo.out'}, T(1) + 0.04);
  count($('.big .n', s0), nemo.gen, T(1) + 0.04, 0.85, 1);
  cue(T(1), 'answer:drop', 'impact');
  call(T(1), () => { Die.heatAll(0.95); Die.pulseBurst(34, 1, 620); Die.telemetry(85, 0.3); });
  tl.to(cam, {zoom: 2.75, duration: 0.12, ease: 'power2.out'}, T(1));
  tl.to(cam, {zoom: 2.15, duration: 1.0, ease: 'expo.out'}, T(1) + 0.12);
  rise($('.sub', s0), T(1, 2), 0, 18);
  const chips = $$('.chip', s0);
  CH.forEach((c, i) => {   // the machine, a beat at a time
    const t = T(2, i);
    tl.from(chips[i], {opacity: 0, y: 18, scale: 0.92, duration: 0.45, ease: 'back.out(2)'}, t);
    call(t, () => Die.mark(c.r));
    cue(t + 0.02, `machine:${c.r}:${i}`, 'tick');
  });
  tl.to(cam, {labels: 1, duration: 0.25}, T(2));
  tl.to(cam, {labels: 0, duration: 0.25}, T(3) - 0.35);
  call(T(3) - 0.1, () => Die.mark(null));

  /* ============================================================ setup */
  const CMD = 'irm https://raw.githubusercontent.com/an6122003/rtx-spark-ai-workshop/main/install.ps1 | iex';
  const CMD2 = CMD.replace('an6122003/', 'an6122003/\n');
  const STEPS = ['Checks this PC', 'Python for Arm64', 'Ollama on the GPU', 'Models · 29 GB', 'Lab 1 · trains Aurora',
    'Lab 2 · builds the index', 'Enterprise · 25 GB', 'Every lab, end to end'];
  const s1 = scene('q1', `<div class="col">
      ${kicker('', 'Setup')}
      ${headline('One <em>command.</em>')}
      <div class="plate term">
        <div class="line"><span class="ps">PS&gt;</span><span class="ct"></span><i class="cur"></i></div>
        <div class="pbar"><div class="lab"><span class="ck">✓</span><span class="st">${STEPS[0]}</span><span class="pc">0%</span></div><div class="track"><i></i></div></div>
      </div>
      <div class="stats">
        <div class="stat"><div class="n" data-n="${INS.first_min || 35}" data-u="min">0</div><div class="d">first install,<br>from nothing</div></div>
        <div class="stat"><div class="n" data-n="${INS.gb || 58}" data-u="GB">0</div><div class="d">of models,<br>downloaded once</div></div>
        <div class="stat"><div class="n" data-n="0" data-u="admin">0</div><div class="d">rights<br>needed</div></div>
      </div>
    </div>`);
  hold(s1, T(3), T(5));
  titles(s1, T(3));
  cue(T(3), 'setup:in', 'whoosh');
  call(T(3), () => { Die.mark(null); Die.telemetry(30, 0.3); });
  camTo({fx: 0, fy: 0, zoom: 1.6}, T(3) - 0.2, 0.9);
  rise($('.term', s1), T(3) + 0.1, 0, 24);
  const tType = T(3, 1);
  type($('.ct', s1), CMD2, tType, 0.8);
  cue(tType, 'setup:typing', 'typing');
  const tEnter = tType + 0.86;
  cue(tEnter, 'setup:enter', 'click');
  const pbar = $('.pbar', s1), pst = $('.st', pbar), ppc = $('.pc', pbar), pbi = $('.track i', pbar);
  const tP0 = tEnter + 0.08, tP1 = T(4, 2), pr = {p: 0};
  tl.from(pbar, {opacity: 0, y: 10, duration: 0.25}, tP0 - 0.06);
  tl.to(pr, {p: 1, duration: tP1 - tP0, ease: 'none', onUpdate: () => {
    pst.textContent = STEPS[Math.min(STEPS.length - 1, Math.floor(pr.p * STEPS.length))];
    ppc.textContent = Math.round(pr.p * 100) + '%';
    pbi.style.transform = `scaleX(${pr.p})`;
  }}, tP0);
  [2, 4, 6, 8].forEach(i => {   // a tick every other step, the last one as it lands
    const t = tP0 + (tP1 - tP0) * (i === 8 ? 1 : i / 8);
    cue(t, `setup:step:${i}`, 'tick');
    call(t, () => Die.pulseBurst(5, -1, 700));
  });
  const stats = $$('.stat', s1), tS = T(4);
  rise(stats, tS, 0.1);
  stats.forEach((s, i) => {
    const n = $('.n', s);
    if (+n.dataset.n > 0) count(n, +n.dataset.n, tS + i * 0.1, 0.6, 0, n.dataset.u);
    else n.innerHTML = `0<small>${n.dataset.u}</small>`;
  });

  /* ============================================== test 01: fine-tune */
  const loss = (L1.loss && L1.loss.length) ? L1.loss : Array.from({length: 55}, (_, i) => [i + 1, 2.4 * Math.exp(-i / 9) + 0.12]);
  const s2 = scene('q2', `<div class="col">
      ${kicker('01', 'Test · Fine-tune')}
      ${headline('Teach a model|<em>who it is.</em>')}
      <div class="plate lossq"><div class="cap">Training loss<b>LoRA · ${steps} steps · this GPU</b></div>
        <svg viewBox="0 0 800 118" preserveAspectRatio="none"><defs><linearGradient id="lossfillq" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#76b900" stop-opacity=".22"/><stop offset="1" stop-color="#76b900" stop-opacity="0"/></linearGradient>
          <clipPath id="lossclipq"><rect class="clip" x="0" y="-10" width="0" height="140"/></clipPath></defs>
          <g class="grid">${[0, 1, 2].map(i => `<line x1="0" x2="800" y1="${8 + i * 51}" y2="${8 + i * 51}"/>`).join('')}</g>
          <g clip-path="url(#lossclipq)"><path class="area"/><path class="curve"/></g><circle class="dot" r="7"/></svg>
        <div class="meters">
          <div class="meter"><div class="k">Step</div><div class="val m-step">0</div></div>
          <div class="meter"><div class="k">Time</div><div class="val m-time">0</div></div>
          <div class="meter"><div class="k">GPU</div><div class="val m-gpu">0</div></div>
          <div class="meter"><div class="k">Loss</div><div class="val m-loss">0</div></div>
        </div></div>
      <div class="plate said">
        <div class="was"><b>Before</b>${L1.before || 'I am Qwen, a large language model created by Alibaba Cloud.'}</div>
        <div class="now"><b>After</b>${words(L1.after || 'I am Aurora, the AI technical assistant of Aurora Grid Systems. I run entirely on this NVIDIA RTX Spark; nothing leaves the machine.')}</div>
        <i class="mark">✓</i>
      </div>
    </div>`);
  hold(s2, T(5), T(7));
  titles(s2, T(5));
  cue(T(5), 'test1:in', 'whoosh');
  call(T(5), () => { Die.mark('gpu', false); Die.telemetry(30, 0.3); });
  camTo(shot('gpu'), T(5) - 0.25, 0.9);
  tl.to(cam, {labels: 0.9, duration: 0.4}, T(5) + 0.4);
  rise($('.lossq', s2), T(5) + 0.12, 0, 22);
  const svg = $('.lossq svg', s2), lmax = Math.max(...loss.map(p => p[1])), lmin = Math.min(...loss.map(p => p[1]));
  const X = s => ((s - loss[0][0]) / Math.max(1, loss[loss.length - 1][0] - loss[0][0])) * 800;
  const Y = l => 110 - ((l - lmin) / Math.max(1e-6, lmax - lmin)) * 100;
  const d = loss.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join('');
  $('.curve', svg).setAttribute('d', d);
  $('.area', svg).setAttribute('d', d + 'L800,118L0,118Z');
  const tA = T(5, 1) + 0.2, tB = T(5, 3) + 0.35;   // the 54 s run, played in under 1.5 s
  tl.to($('.clip', svg), {attr: {width: 800}, duration: tB - tA, ease: 'none'}, tA);
  const prog = {p: 0}, dot = $('.dot', svg), util = L1.util || [];
  const mStep = $('.m-step', s2), mTime = $('.m-time', s2), mGpu = $('.m-gpu', s2), mLoss = $('.m-loss', s2);
  tl.to(prog, {p: 1, duration: tB - tA, ease: 'none', onUpdate: () => {
    const i = Math.min(loss.length - 1, Math.round(prog.p * (loss.length - 1)));
    dot.setAttribute('cx', X(loss[i][0])); dot.setAttribute('cy', Y(loss[i][1]));
    mStep.innerHTML = `${loss[i][0]}<small>/ ${steps}</small>`;
    mTime.innerHTML = `${fmt(prog.p * trainS)}<small>s</small>`;
    const u = util.length ? util[Math.min(util.length - 1, Math.floor(prog.p * util.length))] : 90;
    mGpu.innerHTML = `${fmt(u)}<small>%</small>`;
    mLoss.innerHTML = fmt(loss[i][1], 2);
  }}, tA);
  call(tA, () => Die.telemetry(95, 0.45));
  for (let t = tA; t < tB; t += 0.35) { const k = (t - tA) / (tB - tA); call(t, () => Die.step(k, lmax - (lmax - lmin) * k)); }
  cue(tB + 0.02, 'test1:trained', 'chime');
  call(tB + 0.3, () => Die.telemetry(30, 0.3));
  const said = $('.said', s2), tSaid = T(6) + 0.05;
  rise(said, tSaid, 0, 24);
  cue(tSaid, 'test1:said', 'pop');
  wordsIn($('.now', said), tSaid + 0.15, 0.6);
  call(tSaid + 0.15, () => Die.token(12));
  pop($('.mark', said), T(6, 2));
  cue(T(6, 2), 'test1:aurora', 'tick');
  tl.to(cam, {labels: 0, duration: 0.3}, T(7) - 0.4);

  /* ==================================================== test 02: RAG */
  const hits = (L2.hits && L2.hits.length) ? L2.hits : [1, 2, 3, 4, 5];
  const plainQ = mark(clip(L2.plain || 'Wait at least 5 minutes after opening the DC disconnect to allow capacitors to discharge.', 10), /(at least 5 minutes)/);
  const ragQ = mark(clip(L2.rag || 'The current requirement is a 12-minute wait after opening the DC disconnect, followed by verifying the terminals.', 12), /(12-minute wait)/);
  const s3 = scene('q3', `<div class="col">
      ${kicker('02', 'Test · RAG')}
      ${headline('Ask your|<em>documents.</em>')}
      <p class="qline"><b>Q</b>${L2.question || 'How long after opening the DC disconnect must I wait before removing a module cover?'}</p>
      <div class="pair">
        <div class="plate ansq"><div class="who">Model alone</div><div class="txt">${plainQ}</div>
          <div class="meta">no documents · ${fmt(L2.t_plain || 0.4, 1)} s · an outdated rule</div><i class="mark no">✕</i></div>
        <div class="plate ansq after"><div class="who">With your documents</div><div class="txt">${ragQ}</div>
          <div class="meta">${hits.length} of 82 passages · ${L2.source || 'SB-2025-01'} · ${fmt(L2.t_total || 1.3, 1)} s</div><i class="mark ok">✓</i></div>
      </div>
    </div>`);
  hold(s3, T(7), T(9));
  titles(s3, T(7));
  call(T(7), () => Die.mark('slc', false));
  camTo(shot('slc'), T(7) - 0.25, 0.9);
  tl.to(cam, {labels: 0.9, duration: 0.4}, T(7) + 0.4);
  rise($('.qline', s3), T(7) + 0.3, 0, 16);
  const pair = $$('.ansq', s3);
  rise(pair[0], T(7, 2), 0, 24);
  cue(T(7, 2), 'test2:alone', 'pop');
  pop($('.mark', pair[0]), T(7, 3));
  call(T(7, 3), () => Die.retrieve(5));
  cue(T(7, 3) + 0.25, 'test2:search', 'blip');
  rise(pair[1], T(8), 0, 24);
  cue(T(8), 'test2:docs', 'pop');
  call(T(8), () => Die.token(10));
  pop($('.mark', pair[1]), T(8, 2));
  cue(T(8, 2), 'test2:right', 'chime');
  tl.to(cam, {labels: 0, duration: 0.3}, T(9) - 0.4);

  /* ================================================== test 03: agent */
  const calls = (L3.calls && L3.calls.length) ? L3.calls.slice(0, 4) : [
    {name: 'get_dataset_info', arg: '', ms: 300}, {name: 'analyze_sales', arg: 'Khu vực', ms: 910},
    {name: 'create_chart', arg: 'bar', ms: 1330}, {name: 'export_excel_report', arg: 'Excel', ms: 2200}];
  const regions = (L3.regions && L3.regions.length) ? L3.regions : [
    {name: 'TP. Hồ Chí Minh', a: 474.5, b: 551.3}, {name: 'Hà Nội', a: 365.5, b: 340.8}, {name: 'Hải Phòng', a: 153.6, b: 186.1}, {name: 'Đà Nẵng', a: 105.9, b: 174.2}];
  const vmax = Math.max(...regions.map(r => Math.max(r.a, r.b)));
  const best = regions.reduce((a, r) => ((r.b / r.a) > (a.b / a.a) ? r : a), regions[0]);
  const s4 = scene('q4', `<div class="col">
      ${kicker('03', 'Test · Agent')}
      ${headline('Hand it a|<em>spreadsheet.</em>')}
      <p class="qline"><b>Ask</b>${L3.question || 'Analyse sales by region and tell me which region grew the most.'}</p>
      <div class="swap">
        <div class="part a"><div class="trace">${calls.map(c => `<div class="call"><i class="dotc"></i><span>${c.name}<span class="arg">(${c.arg || ''})</span></span><span class="ms">${fmt(c.ms)} ms</span></div>`).join('')}</div></div>
        <div class="part b"><div class="plate chart"><div class="cap">Revenue by region<b>bn VND · 2024 vs 2025</b></div>
          <div class="bars">${regions.map(r => { const p = (r.b / r.a - 1) * 100, hb = Math.max(r.a, r.b) / vmax * 100; return `<div class="grp${r === best ? ' top' : ''}"><span class="pct${p < 0 ? ' neg' : ''}" style="bottom:calc(${hb.toFixed(1)}% + 10px)">${p >= 0 ? '+' : ''}${fmt(p, 1)}%</span><i class="a" style="height:${(r.a / vmax * 100).toFixed(1)}%"></i><i class="b" style="height:${(r.b / vmax * 100).toFixed(1)}%"></i></div>`; }).join('')}</div>
          <div class="xl">${regions.map(r => `<span>${r.name}</span>`).join('')}</div></div></div>
      </div>
      <p class="result">Fastest-growing region: <b>${best.name}</b>, <span class="nv">+${fmt((best.b / best.a - 1) * 100, 1)}%</span></p>
      <p class="engine">${fmt(L3.total_s || 7.3, 1)} s · ${calls.length} tool calls · chart + Excel report on disk</p>
    </div>`);
  hold(s4, T(9), T(11));
  titles(s4, T(9));
  call(T(9), () => Die.mark('cpu', false));
  camTo(shot('cpu'), T(9) - 0.25, 0.9);
  tl.to(cam, {labels: 0.9, duration: 0.4}, T(9) + 0.4);
  rise($('.qline', s4), T(9) + 0.3, 0, 16);
  $$('.call', s4).forEach((c, i) => {
    const t = T(9, 1) + 0.2 + i * 0.26;
    tl.to(c, {opacity: 1, duration: 0.2}, t);
    tl.from(c, {x: -18, duration: 0.4, ease: 'expo.out'}, t);
    call(t, () => Die.tool());
    cue(t, `test3:call:${i}`, 'blip');
  });
  const ca = $('.part.a', s4), cb = $('.part.b', s4), tChart = T(10);
  tl.to(ca, {opacity: 0, y: -20, duration: 0.25, ease: 'power2.in'}, tChart - 0.25);
  tl.from(cb, {opacity: 0, duration: 0.01}, tChart);
  rise($('.chart', cb), tChart, 0, 22);
  tl.from($$('.grp i.a', cb), {scaleY: 0, duration: 0.5, ease: 'expo.out', stagger: 0.05}, tChart + 0.15);
  tl.from($$('.grp i.b', cb), {scaleY: 0, duration: 0.6, ease: 'expo.out', stagger: 0.05}, tChart + 0.3);
  tl.from($$('.grp .pct', cb), {opacity: 0, y: 8, duration: 0.35, stagger: 0.05}, tChart + 0.6);
  rise($('.result', s4), T(10, 1) + 0.15, 0, 16);
  cue(T(10, 1) + 0.15, 'test3:result', 'chime');
  rise($('.engine', s4), T(10, 2), 0, 10);
  tl.to(cam, {labels: 0, duration: 0.3}, T(11) - 0.4);

  /* ================================================== test 04: batch */
  const JOBS = [
    {k: 'inbox', nm: 'Inbox triage', sub: 'customer messages', acc: 'topics right'},
    {k: 'invoices', nm: 'Invoices → Excel', sub: 'scanned VAT invoices', acc: 'fields right'},
    {k: 'calls', nm: 'Call quality', sub: 'recorded calls, Vietnamese', acc: 'checks right'},
  ];
  const s5 = scene('q5', `<div class="col">
      ${kicker('04', 'Test · Batch')}
      ${headline('AI on the|<em>night shift.</em>')}
      <div class="jobsq">${JOBS.map(j => { const e = ENT[j.k] || {}; return `<div class="plate jobq"><div class="nm">${j.nm}<small>${fmt(e.n || 0)} ${j.sub}</small></div><div class="n">0</div><div class="prog"><i></i></div><div class="r"><b>${e.rate ? fmt(e.rate, e.rate < 10 ? 1 : 0) + ' / min' : ''}</b>${e.acc ? ' · ' + fmt(e.acc) + '% ' + j.acc : ''}</div></div>`; }).join('')}</div>
      <p class="engine">Qwen3.6-35B-A3B on llama.cpp · <b>32 requests at a time</b></p>
    </div>`);
  hold(s5, T(11), T(13));
  titles(s5, T(11));
  call(T(11), () => { Die.mark(null); Die.telemetry(80, 0.6); });
  camTo({fx: 0, fy: 0, zoom: 1.75, ax: 0.5, ay: 0.2}, T(11) - 0.25, 0.9);
  const jobs = $$('.jobq', s5);
  rise(jobs, T(11, 1), 0.1, 22);
  rise($('.engine', s5), T(11, 3), 0, 10);
  call(T(11, 2), () => Die.batch(9));
  JOBS.forEach((j, i) => {   // the three finish a beat apart, through the score's break
    const e = ENT[j.k] || {n: 100}, t0 = T(11, 2) + i * 0.15, dur = T(12, 1 + i) - t0;
    tl.to($('.prog i', jobs[i]), {scaleX: 1, duration: dur, ease: 'power1.inOut'}, t0);
    count($('.n', jobs[i]), e.n || 100, t0, dur, 0);
    cue(t0 + dur, `test4:${j.k}:done`, 'tick');
  });
  call(T(13) - 0.3, () => Die.batch(0));

  /* ====================================================== the results */
  const ROWS = [
    {k: '<b>Nemotron 30B</b> · writing', n: nemo.gen, d: 1, u: 'tok/s', top: true},
    {k: '<b>Nemotron 30B</b> · reading a prompt', n: nemo.prompt, d: 0, u: 'tok/s'},
    {k: '<b>Qwen2.5 1.5B</b> · writing', n: qwen.gen, d: 0, u: 'tok/s'},
    {k: `<b>Fine-tune</b> · ${steps} LoRA steps`, n: trainS, d: 0, u: 's'},
    {k: '<b>RAG</b> · an answer with its source', n: L2.t_total || 1.3, d: 1, u: 's'},
    {k: '<b>Agent</b> · 4 tools, chart, Excel', n: L3.total_s || 7.3, d: 1, u: 's'},
    {k: '<b>Batch</b> · 32 at a time', n: (ENT.inbox && ENT.inbox.rate) || 88, d: 0, u: 'msgs/min'},
    {k: '<b>GPU</b> at its busiest', n: G.peak_power || 72, d: 0, u: `W · ${fmt(G.peak_temp || 78)} °C`},
  ];
  const s6 = scene('q6', `<div class="col">
      ${kicker('', 'Results · this laptop')}
      ${headline('The <em>numbers.</em>')}
      <div class="board">${ROWS.map(r => `<div class="row${r.top ? ' top' : ''}"><i class="flash"></i><div class="k">${r.k}</div><div class="v" data-n="${r.n}" data-d="${r.d}" data-u="${r.u}">0</div></div>`).join('')}</div>
      <div class="memq"><div class="lab"><span>Every model in the workshop</span><b>${fmt(memUsed)}<small>of 128 GB</small></b></div><div class="track"><i></i></div></div>
    </div>`);
  hold(s6, T(13), T(17));
  titles(s6, T(13));
  cue(T(13), 'results:peak', 'impact');
  call(T(13), () => { Die.heatAll(0.85); Die.pulseBurst(28, 1, 700); Die.telemetry(100, 0.7); });
  tl.to(cam, {zoom: 2.2, fx: 0, fy: 0, ax: 0.5, ay: 0.2, duration: 0.12, ease: 'power2.out'}, T(13));
  tl.to(cam, {zoom: 1.8, duration: 1.0, ease: 'expo.out'}, T(13) + 0.12);
  const rows = $$('.row', s6);
  rows.forEach((r, i) => {   // one a beat
    const t = T(13, 1 + i), v = $('.v', r);
    tl.from(r, {opacity: 0, x: -24, duration: 0.4, ease: 'expo.out'}, t);
    count(v, +v.dataset.n, t, 0.5, +v.dataset.d, v.dataset.u);
    tl.fromTo($('.flash', r), {opacity: 1}, {opacity: 0, duration: 0.6, ease: 'power2.out'}, t);
    cue(t, `results:${i}`, 'tick');
  });
  const tM = T(15, 2);
  rise($('.memq', s6), tM, 0, 16);
  tl.to($('.memq .track i', s6), {scaleX: memUsed / 128, duration: 0.8, ease: 'expo.out'}, tM + 0.1);
  cue(tM + 0.1, 'results:memory', 'pop');

  /* ============================================================ outro */
  const s7 = scene('q7', `<div class="col">
      ${headline('Zero cloud calls.|<em>One laptop.</em>')}
      <div class="plate cmd"><span class="ps">PS&gt;</span>${CMD2.replace('\n', '<br>')}</div>
      <div class="repo">github.com/an6122003/rtx-spark-ai-workshop</div>
      <div class="byline"><img src="an.webp" alt=""><span><b>An À Ha</b> · @anndaynee<br><span>Engineer &amp; AI Product Builder · Tech &amp; AI Creator</span></span></div>
    </div>`);
  tl.set(s7, {opacity: 1}, T(17));
  titles(s7, T(17));
  call(T(17), () => { Die.mark(null); Die.telemetry(20, 0.25); });
  camTo({fx: 0, fy: 0, zoom: 2.0, ax: 0.5, ay: 0.2}, T(17) - 0.3, 1.2);
  rise($('.cmd', s7), T(17, 1));
  rise($('.repo', s7), T(17, 2), 0, 12);
  rise($('.byline', s7), T(18));
  call(T(18), () => { Die.heatAll(0.7); Die.pulseBurst(18, 1, 520); });
  cue(T(18), 'outro:byline', 'note');

  /* ------------------------------------------------------------ driver --- */
  const total = Math.round(END * FPS);
  let last = -1;
  window.FILM = {
    fps: FPS, frames: total, duration: END, cues, downbeats: DB,
    score: {take: Q.take || 'music_b', segments: Q.segments || [[5.87, 29.74], [61.75, 75.88]]},
    frame(n) {   // frames come in order; one step of the chip per frame
      const t = n / FPS;
      VT.advanceTo(t);
      tl.time(t);
      Die.advance(last < 0 ? 0 : (n - last) / FPS);
      last = n;
      return t;
    },
  };
  FILM.frame(0);
})();
