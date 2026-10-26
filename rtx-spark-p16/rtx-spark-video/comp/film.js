/* The film: one GSAP timeline on the film's own clock, cut to the score's bars.
 *
 *   index.html?f=h   1920x1080        index.html?f=v   1080x1920
 *
 * render.ps1 calls window.FILM.frame(n) for every frame and captures the page. Every number on screen comes from
 * data.js, written by bench/make_data.py from what was measured on this laptop; the bar grid is earshot's beat
 * tracking of the ElevenLabs score (entered 4 s in, so its drop lands on the title).
 *
 * The score, in film time: a build to the drop at 4 s; breaks at 26-28 s and 58-60 s; its peak from 60 s;
 * a fade to silence from 68 s to 72 s.
 */
(function () {
  'use strict';
  const V = new URLSearchParams(location.search).get('f') === 'v';
  document.body.classList.add(V ? 'v' : 'h');
  const D = window.DATA || {};
  const FPS = 30, END = 72;
  const DB = (D.music && D.music.downbeats) || null;
  function T(bar, beat) {   // a time on the score's bars (bar 2 = the drop)
    const x = bar + (beat || 0) / 4;
    if (!DB) return x * 2;
    const i = Math.max(0, Math.min(DB.length - 2, Math.floor(x)));
    return DB[i] + (x - i) * (DB[i + 1] - DB[i]);
  }
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const fmt = (n, d) => Number(n).toLocaleString('en-US', {minimumFractionDigits: d || 0, maximumFractionDigits: d || 0});
  const pick = (h, v) => (V ? v : h);
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
  const headline = s => '<h1 class="h1">' + s.split('|').map(l => `<span class="ln"><span class="li">${l}</span></span>`).join('') + '</h1>';
  const kicker = (idx, text) => `<div class="kicker">${idx ? `<span class="idx">${idx}</span>` : ''}<span>${text}</span><i class="rule"></i></div>`;
  const words = s => s.split(/(\s+)/).map(w => (/^\s+$/.test(w) ? w : `<span class="w">${w}</span>`)).join('');

  function hold(el, t0, t1) {
    tl.set(el, {opacity: 1}, t0);
    tl.to(el, {opacity: 0, duration: 0.45, ease: 'power2.in'}, t1 - 0.45);
  }
  function titles(el, t) {
    const k = $('.kicker', el);
    if (k) {
      tl.from(k, {opacity: 0, letterSpacing: '0.62em', duration: 1.1, ease: 'expo.out'}, t);
      tl.from($('.rule', k), {scaleX: 0, duration: 1.1, ease: 'expo.out'}, t + 0.15);
    }
    tl.from($$('.h1 .li', el), {yPercent: 118, duration: 1.1, ease: 'expo.out', stagger: 0.1}, t + 0.1);
    const em = $$('.h1 em', el);
    if (em.length) tl.from(em, {fontWeight: 200, duration: 1.6, ease: 'power2.out'}, t + 0.45);
  }
  function rise(targets, t, stagger, dist) {
    tl.from(targets, {opacity: 0, y: dist == null ? 34 : dist, duration: 0.9, ease: 'expo.out', stagger: stagger || 0}, t);
  }
  function count(el, to, t, dur, dec, unit) {
    const o = {v: 0}, u = unit ? `<small>${unit}</small>` : '';
    el.innerHTML = fmt(0, dec) + u;
    tl.to(o, {v: to, duration: dur || 0.9, ease: 'power3.out', onUpdate: () => { el.innerHTML = fmt(o.v, dec) + u; }}, t);
  }
  function type(el, text, t, dur) {
    const o = {n: 0};
    tl.to(o, {n: text.length, duration: dur, ease: 'none', onUpdate: () => { el.textContent = text.slice(0, Math.round(o.n)); }}, t);
  }
  function wordsIn(el, t, dur) {
    const ws = $$('.w', el);
    tl.to(ws, {opacity: 1, duration: 0.18, ease: 'none', stagger: ws.length > 1 ? dur / ws.length : 0}, t);
  }
  const call = (t, fn) => tl.call(fn, null, t);
  const cam = Die.cam;
  function camTo(vars, t, dur, ease) { tl.to(cam, Object.assign({duration: dur == null ? 1.4 : dur, ease: ease || 'expo.inOut'}, vars), t); }
  function shot(region, h, v) {
    const s = Die.shot(region), a = pick(h, v);
    return {fx: s.fx, fy: s.fy, zoom: s.zoom * a.k, ax: a.ax, ay: a.ay};
  }
  function swapParts(a, b, tOut, tIn) {
    tl.to(a, {opacity: 0, y: -24, duration: 0.42, ease: 'power2.in'}, tOut);
    tl.from(b, {opacity: 0, duration: 0.01}, tIn);
  }

  /* ------------------------------------------------------------- data --- */
  const O = D.ollama || {};
  const L1 = D.lab1 || {}, L2 = D.lab2 || {}, L3 = D.lab3 || {}, ENT = D.ent || {}, G = D.gpu || {}, MEM = D.mem || {};
  const nemo = O.nemotron || {gen: 82.9, prompt: 2238}, qwen = O.qwen || {gen: 150}, emb = O.embed || 9;
  const trainS = L1.train_s || 40, steps = L1.steps || 55;

  /* ------------------------------------------------------- the chip --- */
  Die.init($('#die'));
  Die.configure({sm: 48, cores: 20, gpuCores: 6144, memGb: 128, label: 'RTX Spark N1X'});
  Die.labelScale(pick(1.75, 2.1));
  Object.assign(cam, {ax: pick(0.7, 0.5), ay: pick(0.5, 0.25), fx: 0, fy: 0, zoom: pick(2.6, 3.2), alpha: 1, labels: 0});

  /* ============================================================ intro */
  const s0 = scene('s0', `<div class="col">
      ${kicker('', 'On-device AI · NVIDIA RTX Spark')}
      ${headline('Everything|runs <em>here.</em>')}
      <p class="lead">Fine-tune a model, ask your documents, hand an agent a spreadsheet and run batch AI. One laptop. Zero cloud calls.</p>
    </div>`);
  hold(s0, 0, T(3));
  call(0.05, () => Die.boot());
  tl.from($('.kicker', s0), {opacity: 0, letterSpacing: '0.7em', duration: 1.6, ease: 'expo.out'}, T(0, 2));
  tl.from($('.kicker .rule', s0), {scaleX: 0, duration: 1.4, ease: 'expo.out'}, T(0, 3));
  camTo({zoom: pick(1.15, 1.5)}, 0.2, T(2) - 0.2, 'power2.inOut');
  tl.from($$('.h1 .li', s0), {yPercent: 118, duration: 1.0, ease: 'expo.out', stagger: 0.09}, T(2) - 0.06);
  tl.from($('.h1 em', s0), {fontWeight: 200, duration: 1.6, ease: 'power2.out'}, T(2) + 0.3);
  call(T(2), () => { Die.heatAll(0.95); Die.pulseBurst(34, 1, 620); Die.telemetry(35, 0.25); });
  cue(T(2), 'intro:drop', 'impact');
  tl.to(cam, {labels: 1, duration: 0.8}, T(2) + 0.4);
  rise($('.lead', s0), T(2, 2));
  tl.to(cam, {labels: 0, duration: 0.5}, T(3) - 0.6);

  /* ========================================================== machine */
  const SPECS = [
    {v: 6144, f: n => fmt(n), t: 'CUDA cores', d: 'NVIDIA Blackwell RTX GPU', r: 'gpu'},
    {v: 20, f: n => fmt(n), t: 'CPU cores', d: 'NVIDIA Grace, Arm', r: 'cpu'},
    {v: 128, f: n => fmt(n) + ' GB', t: 'Unified memory', d: 'LPDDR5X, shared by CPU and GPU', r: 'mem'},
    {v: 1, f: n => fmt(n) + ' PFLOP', t: 'AI performance', d: 'Fifth-generation Tensor Cores', r: 'gpu'},
    {v: null, s: 'NPU', t: 'On the same chip', d: 'A neural processing unit', r: 'npu'},
    {v: null, s: '45–80 W', t: 'The whole chip', d: 'Within a laptop’s power budget', r: 'pkg'},
  ];
  const s1 = scene('s1', `<div class="col">
      ${kicker('', 'The machine')}
      ${headline('One <em>superchip.</em>')}
      <div class="specs">${SPECS.map(s => `<div class="spec"><span class="v">${s.s || '0'}</span><span class="t">${s.t}<small>${s.d}</small></span><i class="bar"></i></div>`).join('')}</div>
    </div>`);
  hold(s1, T(3), T(7));
  titles(s1, T(3));
  const rows = $$('.spec', s1), rowGap = (T(7) - T(3, 2)) / 6.3;
  call(T(3), () => Die.mark(null));
  SPECS.forEach((s, i) => {
    const t = T(3, 2) + i * rowGap, r = rows[i];
    tl.from(r, {opacity: 0, y: 18, duration: 0.6, ease: 'expo.out'}, t - 0.15);
    call(t, () => { rows.forEach(x => x.classList.remove('on')); r.classList.add('on'); Die.mark(s.r); });
    tl.fromTo($('.bar', r), {scaleX: 0}, {scaleX: 1, duration: rowGap, ease: 'none'}, t);
    tl.set($('.bar', r), {scaleX: 0}, t + rowGap);
    camTo(shot(s.r, {ax: 0.73, ay: 0.5, k: 1}, {ax: 0.5, ay: 0.24, k: 1.25}), t - 0.25, 0.95);
    if (s.v != null) {
      const o = {n: 0}, el = $('.v', r);
      tl.to(o, {n: s.v, duration: 0.7, ease: 'power3.out', onUpdate: () => { el.textContent = s.f(Math.round(o.n)); }}, t);
      cue(t + 0.7, `machine:${s.r}:${i}`, 'tick');
    } else cue(t + 0.1, `machine:${s.r}:${i}`, 'tick');
    if (i === 0) { tl.to(cam, {labels: 1, duration: 0.4}, t); cue(t - 0.25, 'machine:fly', 'whoosh'); }
  });
  tl.to(cam, {labels: 0, duration: 0.4}, T(7) - 0.5);

  /* ========================================================== install */
  const CMD = 'irm https://raw.githubusercontent.com/an6122003/rtx-spark-ai-workshop/main/install.ps1 | iex';
  const CMD2 = CMD.replace('an6122003/', 'an6122003/\n');   // wrapped where a reader would, not mid-word
  const STEPS = ['Checks this PC', 'Python for Arm64', 'Ollama on the GPU', 'Models · 29 GB', 'Lab 1 · trains Aurora',
    'Lab 2 · builds the index', 'Enterprise · 25 GB', 'Every lab, end to end'];
  const ins = D.install || {first_min: 35, gb: 58};
  const s2 = scene('s2', `<div class="col">
      ${kicker('', 'Setup')}
      ${headline('One command.|<em>Every lab ready.</em>')}
      <div class="plate term">
        <div class="line"><span class="ps">PS&gt;</span><span class="ct"></span><i class="cur"></i></div>
        <div class="steps8">${STEPS.map(s => `<div class="step8"><span class="ck">✓</span><span>${s}</span></div>`).join('')}</div>
      </div>
      <div class="stats">
        <div class="stat"><div class="n" data-n="${ins.first_min}" data-u="min">0</div><div class="d">first install,<br>from nothing</div></div>
        <div class="stat"><div class="n" data-n="${ins.gb}" data-u="GB">0</div><div class="d">of models,<br>downloaded once</div></div>
        <div class="stat"><div class="n" data-n="0" data-u="admin">0</div><div class="d">rights or Developer<br>Mode needed</div></div>
      </div>
    </div>`);
  hold(s2, T(7), T(10));
  titles(s2, T(7));
  call(T(7), () => { Die.mark(null); Die.telemetry(25, 0.3); });
  camTo(pick({ax: 0.84, ay: 0.45, fx: 0, fy: 0, zoom: 0.95}, {ax: 0.5, ay: 0.2, fx: 0, fy: 0, zoom: 1.25}), T(7) - 0.3, 1.3);
  rise($('.term', s2), T(7, 1));
  const tType = T(7, 2);
  type($('.ct', s2), CMD2, tType, 1.25);
  cue(tType, 'install:typing', 'typing');
  cue(tType + 1.35, 'install:enter', 'click');
  const st8 = $$('.step8', s2), t8 = tType + 1.5;
  st8.forEach((s, i) => {
    tl.to(s, {opacity: 1, duration: 0.2}, t8 + i * 0.14);
    tl.from(s, {x: -14, duration: 0.45, ease: 'expo.out'}, t8 + i * 0.14);
    if (i % 2 === 1) cue(t8 + i * 0.14, `install:step:${i}`, 'tick');
    call(t8 + i * 0.14, () => Die.pulseBurst(4, -1, 700));
  });
  const stats = $$('.stat', s2), tStats = t8 + 1.15;
  rise(stats, tStats, 0.12);
  stats.forEach((s, i) => {
    const n = $('.n', s);
    if (+n.dataset.n > 0) count(n, +n.dataset.n, tStats + i * 0.12, 0.9, 0, n.dataset.u);
    else n.innerHTML = `0<small>${n.dataset.u}</small>`;
  });

  /* ============================================================ lab 1 */
  const B3 = 10, E3 = 14.5;
  const loss = (L1.loss && L1.loss.length) ? L1.loss : Array.from({length: 55}, (_, i) => [i + 1, 2.4 * Math.exp(-i / 9) + 0.12]);
  const s3 = scene('s3', `<div class="col">
      ${kicker('01', 'Fine-tuning')}
      ${headline('Teach a model|<em>who it is.</em>')}
      <div class="swap">
        <div class="part a">
          <div class="flow"><div class="wire"><i></i></div>
            ${[['86 examples', 'train.jsonl'], ['LoRA on GPU', 'Qwen2.5 1.5B'], ['GGUF', 'q8_0'], ['Ollama', 'aurora'], ['Compare', 'before/after']]
              .map(([a, b]) => `<div class="fnode"><i class="sq"></i><div class="ft">${a}</div><div class="fd">${b}</div></div>`).join('')}
          </div>
          <div class="trainrow">
            <div class="plate loss"><div class="cap">Training loss<b>LoRA r16 · 5 epochs · on this GPU</b></div>
              <svg viewBox="0 0 600 250" preserveAspectRatio="none"><defs><linearGradient id="lossfill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#76b900" stop-opacity=".22"/><stop offset="1" stop-color="#76b900" stop-opacity="0"/></linearGradient>
                <clipPath id="lossclip"><rect class="clip" x="0" y="-10" width="0" height="270"/></clipPath></defs>
                <g class="grid">${[0, 1, 2, 3, 4].map(i => `<line x1="0" x2="600" y1="${12 + i * 56}" y2="${12 + i * 56}"/>`).join('')}</g>
                <g clip-path="url(#lossclip)"><path class="area"/><path class="curve"/></g><circle class="dot" r="7"/></svg></div>
            <div class="meters">
              <div class="meter"><div class="k">Step</div><div class="val m-step">0</div></div>
              <div class="meter"><div class="k">Time</div><div class="val m-time">0</div></div>
              <div class="meter"><div class="k">GPU</div><div class="val m-gpu">0</div></div>
              <div class="meter"><div class="k">Loss</div><div class="val m-loss">0</div></div>
            </div>
          </div>
        </div>
        <div class="part b">
          <p class="qline"><b>Ask both</b>${L1.question || 'Who built you, and what are you for?'}</p>
          <div class="duo">
            <div class="plate side"><div class="who">Before<b>qwen2.5:1.5b-instruct</b></div><div class="txt">${words(L1.before || 'I am Qwen, a large language model created by Alibaba Cloud.')}</div></div>
            <div class="plate side after"><div class="who">After<b>aurora-assistant</b></div><div class="txt">${words(L1.after || 'I am Aurora, the AI technical assistant of Aurora Grid Systems. I run entirely on this NVIDIA RTX Spark; nothing leaves the machine.')}</div><i class="mark ok">✓</i></div>
          </div>
        </div>
      </div>
    </div>`);
  hold(s3, T(B3), T(E3));
  titles(s3, T(B3));
  call(T(B3), () => { Die.mark('gpu', false); Die.telemetry(30, 0.3); });
  camTo(shot('gpu', {ax: 0.8, ay: 0.48, k: 0.85}, {ax: 0.5, ay: 0.21, k: 1.05}), T(B3) - 0.3, 1.4);
  tl.to(cam, {labels: 0.9, duration: 0.6}, T(B3) + 0.6);
  cue(T(B3) - 0.3, 'lab1:fly', 'whoosh');
  const fn = $$('.fnode', s3), wire = $('.flow .wire i', s3);
  rise(fn, T(B3, 1), 0.07, 16);
  const onNode = (i, t) => { call(t, () => fn[i].classList.add('on')); tl.to(wire, {scaleX: i / 4, duration: 0.35, ease: 'power2.out'}, t); };
  onNode(0, T(B3, 2)); onNode(1, T(B3, 3));
  const svg = $('.loss svg', s3), lmax = Math.max(...loss.map(p => p[1])), lmin = Math.min(...loss.map(p => p[1]));
  const X = s => ((s - loss[0][0]) / Math.max(1, loss[loss.length - 1][0] - loss[0][0])) * 600, Y = l => 238 - ((l - lmin) / Math.max(1e-6, lmax - lmin)) * 214;
  const d = loss.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join('');
  $('.curve', svg).setAttribute('d', d);
  $('.area', svg).setAttribute('d', d + 'L600,250L0,250Z');
  rise($('.trainrow', s3), T(B3, 3), 0, 26);
  const tA = T(B3 + 1), tB = T(B3 + 2, 2);
  tl.to($('.clip', svg), {attr: {width: 600}, duration: tB - tA, ease: 'none'}, tA);   // the curve keeps pace with the dot
  const prog = {p: 0}, dot = $('.dot', svg), util = L1.util || [];
  const mStep = $('.m-step', s3), mTime = $('.m-time', s3), mGpu = $('.m-gpu', s3), mLoss = $('.m-loss', s3);
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
  for (let t = tA; t < tB; t += 0.42) { const k = (t - tA) / (tB - tA); call(t, () => Die.step(k, lmax - (lmax - lmin) * k)); }
  onNode(2, tB + 0.1); onNode(3, tB + 0.3); onNode(4, tB + 0.5);
  cue(tB + 0.05, 'lab1:trained', 'chime');
  call(tB + 0.6, () => Die.telemetry(25, 0.3));
  const pa = $('.part.a', s3), pb = $('.part.b', s3), tCmp = T(B3 + 2, 3);
  swapParts(pa, pb, tCmp - 0.2, tCmp + 0.2);
  rise($('.qline', pb), tCmp + 0.2);
  const sides = $$('.side', pb);
  rise(sides, T(B3 + 3), 0.4, 30);
  cue(T(B3 + 3), 'lab1:before', 'pop');
  wordsIn($('.txt', sides[0]), T(B3 + 3) + 0.15, 0.7);
  cue(T(B3 + 3) + 0.4, 'lab1:after', 'pop');
  wordsIn($('.txt', sides[1]), T(B3 + 3) + 0.6, 1.1);
  call(T(B3 + 3) + 0.6, () => Die.token(12));
  tl.from($('.mark', sides[1]), {scale: 0, duration: 0.6, ease: 'back.out(2.2)'}, T(B3 + 3, 3) + 0.1);
  cue(T(B3 + 3, 3) + 0.1, 'lab1:aurora', 'tick');
  tl.to(cam, {labels: 0, duration: 0.4}, T(E3) - 0.5);

  /* ============================================================ lab 2 */
  const B4 = 14.5, E4 = 18.5;
  const Q2 = L2.question || 'How long after opening the DC disconnect must I wait before removing a module cover?';
  const hits = (L2.hits && L2.hits.length) ? L2.hits : [7, 19, 33, 52, 70];
  const s4 = scene('s4', `<div class="col">
      ${kicker('02', 'RAG')}
      ${headline('Ask your|<em>documents.</em>')}
      <p class="qline"><b>Question</b>${Q2}</p>
      <div class="swap">
        <div class="part a"><div class="ragrow">
          <div class="ring"><svg viewBox="-170 -170 340 340">${Array.from({length: 82}, (_, i) => {
            const a = (i / 82) * Math.PI * 2 - Math.PI / 2;
            return `<circle class="doc${hits.includes(i) ? ' hit' : ''}" cx="${(150 * Math.cos(a)).toFixed(1)}" cy="${(150 * Math.sin(a)).toFixed(1)}" r="6"/>`;
          }).join('')}${hits.map(i => { const a = (i / 82) * Math.PI * 2 - Math.PI / 2; return `<line class="beam" x1="0" y1="0" x2="${(144 * Math.cos(a)).toFixed(1)}" y2="${(144 * Math.sin(a)).toFixed(1)}"/>`; }).join('')}<circle class="q" r="10"/></svg></div>
          <div class="pipe">
            <div class="pstep"><span class="n">01</span><span>Embed the question</span><span class="ms">qwen3-embedding</span></div>
            <div class="pstep"><span class="n">02</span><span>Search 82 passages</span><span class="ms">top ${hits.length}</span></div>
            <div class="pstep"><span class="n">03</span><span>Answer with sources</span><span class="ms">${fmt(L2.t_total || 3.6, 1)} s</span></div>
          </div></div></div>
        <div class="part b"><div class="duo">
          <div class="plate side"><div class="who">Without RAG<b>model only</b></div><div class="txt">${words(L2.plain || 'You must wait at least 5 minutes after opening the DC disconnect.')}</div><i class="mark no">✕</i><div class="meta">no documents · ${fmt(L2.t_plain || 0.6, 1)} s</div></div>
          <div class="plate side after"><div class="who">With RAG<b>+ ${hits.length} passages</b></div><div class="txt">${words(L2.rag || 'Wait 12 minutes, then verify the DC bus is below 50 V. The 5-minute rule was withdrawn.')}</div><i class="mark ok">✓</i><div class="meta">${L2.source || 'SB-2025-01'} · ${fmt(L2.t_total || 3.6, 1)} s</div></div>
        </div></div>
      </div>
    </div>`);
  hold(s4, T(B4), T(E4));
  titles(s4, T(B4));
  call(T(B4), () => Die.mark('slc', false));
  camTo(shot('slc', {ax: 0.8, ay: 0.5, k: 0.75}, {ax: 0.5, ay: 0.22, k: 0.95}), T(B4) - 0.3, 1.4);
  tl.to(cam, {labels: 0.9, duration: 0.6}, T(B4) + 0.6);
  rise($('.qline', s4), T(B4, 2));
  const docs = $$('.ring .doc', s4), beams = $$('.ring .beam', s4), ps = $$('.pstep', s4);
  tl.from(docs, {opacity: 0, scale: 0, transformOrigin: '50% 50%', duration: 0.35, stagger: 0.006, ease: 'back.out(2)'}, T(B4, 3));
  tl.from($('.ring .q', s4), {scale: 0, transformOrigin: '50% 50%', duration: 0.5, ease: 'back.out(2)'}, T(B4 + 1));
  rise(ps, T(B4, 3), 0.1, 14);
  call(T(B4 + 1), () => ps[0].classList.add('on'));
  cue(T(B4 + 1), 'lab2:embed', 'blip');
  call(T(B4 + 1, 2), () => { ps[1].classList.add('on'); Die.retrieve(5); });
  beams.forEach((b, i) => tl.fromTo(b, {strokeDasharray: 144, strokeDashoffset: 144}, {strokeDashoffset: 0, duration: 0.3, ease: 'power2.out'}, T(B4 + 1, 2) + i * 0.1));
  cue(T(B4 + 1, 2), 'lab2:search', 'blip');
  call(T(B4 + 2), () => { ps[2].classList.add('on'); Die.token(10); });
  cue(T(B4 + 2), 'lab2:answer', 'blip');
  const qa = $('.part.a', s4), qb = $('.part.b', s4), tAns = T(B4 + 2, 2);
  swapParts(qa, qb, tAns - 0.2, tAns + 0.2);
  const s4s = $$('.side', qb);
  rise(s4s, tAns + 0.2, 0.7, 30);
  cue(tAns + 0.2, 'lab2:without', 'pop');
  wordsIn($('.txt', s4s[0]), tAns + 0.35, 0.6);
  tl.from($('.mark', s4s[0]), {scale: 0, duration: 0.5, ease: 'back.out(2.2)'}, tAns + 0.95);
  cue(tAns + 0.9, 'lab2:with', 'pop');
  wordsIn($('.txt', s4s[1]), tAns + 1.05, 1.0);
  tl.from($('.mark', s4s[1]), {scale: 0, duration: 0.6, ease: 'back.out(2.2)'}, tAns + 2.15);
  cue(tAns + 2.15, 'lab2:correct', 'chime');
  tl.to(cam, {labels: 0, duration: 0.4}, T(E4) - 0.5);

  /* ============================================================ lab 3 */
  const B5 = 18.5, E5 = 22.5;
  const Q3 = L3.question || 'Analyse sales by region and tell me which region grew the most.';
  const calls = (L3.calls && L3.calls.length) ? L3.calls.slice(0, 4) : [
    {name: 'get_dataset_info', arg: '', ms: 1460}, {name: 'analyze_sales', arg: 'Khu vực', ms: 930},
    {name: 'create_chart', arg: 'bar', ms: 1330}, {name: 'export_excel_report', arg: 'Excel', ms: 2200}];
  const regions = (L3.regions && L3.regions.length) ? L3.regions : [
    {name: 'TP. Hồ Chí Minh', a: 474.5, b: 551.3}, {name: 'Hà Nội', a: 365.5, b: 340.8}, {name: 'Hải Phòng', a: 153.6, b: 186.1}, {name: 'Đà Nẵng', a: 105.9, b: 174.2}];
  const vmax = Math.max(...regions.map(r => Math.max(r.a, r.b)));
  const best = regions.reduce((a, r) => ((r.b / r.a) > (a.b / a.a) ? r : a), regions[0]);
  const s5 = scene('s5', `<div class="col">
      ${kicker('03', 'Agent')}
      ${headline('Hand an agent|<em>your spreadsheet.</em>')}
      <p class="qline"><b>Ask</b>${Q3}</p>
      <div class="swap">
        <div class="part a"><div class="trace">${calls.map(c => `<div class="call"><i class="dotc"></i><span>${c.name}<span class="arg">(${c.arg || ''})</span></span><span class="ms">${fmt(c.ms)} ms</span></div>`).join('')}</div></div>
        <div class="part b">
          <div class="plate chart"><div class="cap">Revenue by region<b>bn VND · 2024 vs 2025</b></div>
            <div class="bars">${regions.map(r => { const p = (r.b / r.a - 1) * 100, hb = Math.max(r.a, r.b) / vmax * 100; return `<div class="grp${r === best ? ' top' : ''}"><span class="pct${p < 0 ? ' neg' : ''}" style="bottom:calc(${hb.toFixed(1)}% + 10px)">${p >= 0 ? '+' : ''}${fmt(p, 1)}%</span><i class="a" style="height:${(r.a / vmax * 100).toFixed(1)}%"></i><i class="b" style="height:${(r.b / vmax * 100).toFixed(1)}%"></i></div>`; }).join('')}</div>
            <div class="xl">${regions.map(r => `<span>${r.name}</span>`).join('')}</div>
          </div>
          <p class="result">Fastest-growing region: <b>${best.name}</b>, <span class="nv">+${fmt((best.b / best.a - 1) * 100, 1)}%</span></p>
          <p class="meta engine">${fmt(L3.total_s || 11.6, 1)} s · ${calls.length} tool calls · chart and Excel report on disk</p>
        </div>
      </div>
    </div>`);
  hold(s5, T(B5), T(E5));
  titles(s5, T(B5));
  call(T(B5), () => Die.mark('cpu', false));
  camTo(shot('cpu', {ax: 0.8, ay: 0.5, k: 0.8}, {ax: 0.5, ay: 0.22, k: 1.0}), T(B5) - 0.3, 1.4);
  tl.to(cam, {labels: 0.9, duration: 0.6}, T(B5) + 0.6);
  cue(T(B5) - 0.3, 'lab3:fly', 'whoosh');
  rise($('.qline', s5), T(B5, 2));
  $$('.call', s5).forEach((c, i) => {
    const t = T(B5, 3) + i * 0.5;
    tl.to(c, {opacity: 1, duration: 0.3}, t);
    tl.from(c, {x: -18, duration: 0.5, ease: 'expo.out'}, t);
    call(t, () => Die.tool());
    cue(t, `lab3:call:${i}`, 'blip');
  });
  const ca = $('.part.a', s5), cb = $('.part.b', s5), tChart = T(B5 + 1, 3);
  swapParts(ca, cb, tChart - 0.2, tChart + 0.15);
  rise($('.chart', cb), tChart + 0.15, 0, 26);
  tl.from($$('.grp i.a', cb), {scaleY: 0, duration: 0.65, ease: 'expo.out', stagger: 0.07}, tChart + 0.4);
  tl.from($$('.grp i.b', cb), {scaleY: 0, duration: 0.75, ease: 'expo.out', stagger: 0.07}, tChart + 0.6);
  tl.from($$('.grp .pct', cb), {opacity: 0, y: 10, duration: 0.45, stagger: 0.07}, tChart + 1.1);
  rise($('.result', cb), tChart + 1.5);
  cue(tChart + 1.5, 'lab3:result', 'chime');
  rise($('.engine', cb), tChart + 1.9, 0, 12);
  tl.to(cam, {labels: 0, duration: 0.4}, T(E5) - 0.5);

  /* ======================================================= enterprise */
  const B6 = 22.5, E6 = 26;
  const JOBS = [
    {k: 'inbox', nm: 'Inbox triage', sub: 'customer messages · email, Zalo, Messenger', acc: 'topics right'},
    {k: 'invoices', nm: 'Invoices → Excel', sub: 'scanned VAT invoices, read by vision', acc: 'fields right'},
    {k: 'calls', nm: 'Call quality', sub: 'recorded calls, Vietnamese speech-to-text', acc: 'checks right'},
  ];
  const s6 = scene('s6', `<div class="col">
      ${kicker('04', 'Enterprise')}
      ${headline('AI on the|<em>night shift.</em>')}
      <div class="jobs">${JOBS.map(j => { const e = ENT[j.k] || {}; return `<div class="plate job"><div class="nm">${j.nm}<small>${fmt(e.n || 0)} ${j.sub}</small></div><div class="prog"><i></i></div><div class="cnt"><div class="n">0</div><div class="r">${e.rate ? fmt(e.rate, e.rate < 10 ? 1 : 0) + ' / min' : ''}${e.acc ? ' · ' + fmt(e.acc) + '% ' + j.acc : ''}</div></div></div>`; }).join('')}</div>
      <p class="engine">llama.cpp · <b>Qwen3.6-35B-A3B</b> · 32 requests at a time · GPU at ${fmt(G.ent_power || 60)} W</p>
    </div>`);
  hold(s6, T(B6), T(E6));
  titles(s6, T(B6));
  call(T(B6), () => { Die.mark(null); Die.telemetry(80, 0.6); });
  camTo(pick({ax: 0.79, ay: 0.5, fx: 0, fy: 0, zoom: 1.05}, {ax: 0.5, ay: 0.22, fx: 0, fy: 0, zoom: 1.35}), T(B6) - 0.3, 1.4);
  const jobs = $$('.job', s6);
  rise(jobs, T(B6, 2), 0.12, 26);
  rise($('.engine', s6), T(B6 + 1), 0, 12);
  call(T(B6, 3), () => Die.batch(9));
  JOBS.forEach((j, i) => {
    const e = ENT[j.k] || {n: 100}, t0 = T(B6, 3) + i * 0.2, dur = (T(E6) - 0.9 - t0) * (0.78 + i * 0.1);
    tl.to($('.prog i', jobs[i]), {scaleX: 1, duration: dur, ease: 'power1.inOut'}, t0);
    count($('.cnt .n', jobs[i]), e.n || 100, t0, dur, 0);
    tl.from($('.cnt .r', jobs[i]), {opacity: 0, duration: 0.4}, t0 + dur);
    cue(t0 + dur, `ent:${j.k}:done`, 'tick');
  });
  call(T(E6) - 0.6, () => Die.batch(0));

  /* =================================================== under the hood */
  const B7 = 26, E7 = 30;
  const series = G.series || [], phases = G.phases || [], tmax = series.length ? series[series.length - 1][0] : 1;
  const pmax = Math.max(1, ...series.map(s => s[2] || 0));
  const xs = t => (t / tmax) * 1000, yu = u => 140 - (u / 100) * 130, yp = p => 140 - (p / pmax) * 130;
  const uPath = series.length ? 'M0,140' + series.map(s => `L${xs(s[0]).toFixed(1)},${yu(s[1] || 0).toFixed(1)}`).join('') + 'L1000,140Z' : '';
  const pPath = series.length ? series.map((s, i) => `${i ? 'L' : 'M'}${xs(s[0]).toFixed(1)},${yp(s[2] || 0).toFixed(1)}`).join('') : '';
  const tags = [];   // phases that start within a few seconds of each other share one label
  phases.forEach(p => {
    const x = xs(p.start), last = tags[tags.length - 1];
    if (last && x - last.x1 < 40) { last.text += ' · ' + p.label; last.x1 = x; } else tags.push({x, x1: x, text: p.label});
  });
  const models = (MEM.models || []).filter(m => m.gb >= 0.5);
  const used = models.reduce((a, m) => a + m.gb, 0);
  const cols = 32, cells = [];
  models.forEach((m, mi) => { for (let k = 0; k < Math.round(m.gb); k++) cells.push(mi % 6); });
  while (cells.length < 128) cells.push(-1);
  const s7 = scene('s7', `<div class="col">
      ${kicker('', 'The whole run, measured')}
      ${headline('Under the <em>hood.</em>')}
      <div class="plate timeline"><div class="cap">GPU load and power, every test<b>${fmt(G.minutes || 16)} min · sampled twice a second</b></div>
        <svg viewBox="0 0 1000 150" preserveAspectRatio="none"><defs><linearGradient id="utilfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#76b900" stop-opacity=".35"/><stop offset="1" stop-color="#76b900" stop-opacity=".02"/></linearGradient>
          <clipPath id="tlclip"><rect class="clip" x="0" y="-20" width="0" height="190"/></clipPath></defs>
          <g clip-path="url(#tlclip)"><path class="util" d="${uPath}"/><path class="pow" d="${pPath}"/></g>
          <g class="ph">${phases.map(p => `<line x1="${xs(p.start).toFixed(1)}" x2="${xs(p.start).toFixed(1)}" y1="0" y2="140"/>`).join('')}${tags.map(g => `<text x="${(g.x + 6).toFixed(1)}" y="14">${g.text}</text>`).join('')}</g></svg>
        <div class="legend2"><span><i style="background:#76b900"></i>GPU load</span><span><i style="background:#cfa977"></i>GPU power, peak ${fmt(G.peak_power || 60)} W</span><span>${fmt(G.peak_temp || 70)} °C at the hottest</span></div>
      </div>
      <div class="plate mem"><div class="cap">Unified memory<b>every model in the workshop: ${fmt(used)} of 128 GB</b></div>
        <div class="waffle" style="grid-template-columns:repeat(${cols},1fr)">${cells.map(c => `<i class="${c >= 0 ? 'm' + c : ''}"></i>`).join('')}</div>
        <ul class="legend3">${models.map((m, mi) => `<li><i class="sw m${mi % 6}"></i>${m.name}<b>${fmt(m.gb, 1)} GB</b></li>`).join('')}</ul>
      </div>
    </div>`);
  hold(s7, T(B7), T(E7));
  titles(s7, T(B7));
  call(T(B7), () => { Die.mark(null); Die.telemetry(60, 0.5); });
  camTo(pick({ax: 0.81, ay: 0.5, fx: 0, fy: 0, zoom: 0.85, alpha: 0.7}, {ax: 0.5, ay: 0.13, fx: 0, fy: 0, zoom: 0.8, alpha: 0.6}), T(B7) - 0.4, 1.3);
  rise($('.timeline', s7), T(B7, 2), 0, 26);
  tl.to($('.timeline .clip', s7), {attr: {width: 1000}, duration: T(B7 + 2) - T(B7, 3), ease: 'power2.inOut'}, T(B7, 3));
  tl.from($$('.timeline .ph', s7), {opacity: 0, duration: 0.5}, T(B7 + 1, 2));
  rise($('.plate.mem', s7), T(B7 + 1, 3), 0, 26);
  tl.from($$('.waffle i', s7), {opacity: 0, scale: 0.3, duration: 0.35, stagger: 0.006, ease: 'back.out(2)'}, T(B7 + 2));
  tl.from($$('.legend3 li', s7), {opacity: 0, x: -10, duration: 0.4, stagger: 0.08}, T(B7 + 2, 2));
  cue(T(B7 + 2), 'hood:memory', 'pop');

  /* ======================================================= the numbers */
  const B8 = 30, E8 = 33.5;
  const M = [
    {n: nemo.gen, d: 1, u: 'tok/s', t: '<b>Nemotron 3.5 Lightning 30B</b>, writing', w: 55},
    {n: nemo.prompt, d: 0, u: 'tok/s', t: 'the same model <b>reading a prompt</b>', w: 100},
    {n: qwen.gen, d: 0, u: 'tok/s', t: '<b>Qwen2.5 1.5B</b>, writing', w: 80},
    {n: emb, d: 1, u: '/s', t: '<b>passages embedded</b> for search', w: 45},
    {n: trainS, d: 0, u: 's', t: `<b>fine-tune</b>: ${steps} LoRA steps on the GPU`, w: 40},
    {n: L2.t_total || 3.6, d: 1, u: 's', t: '<b>RAG</b>: question to a cited answer', w: 30},
    {n: L3.total_s || 11.6, d: 1, u: 's', t: '<b>agent</b>: 4 tool calls, chart, Excel', w: 45},
    {n: (ENT.inbox && ENT.inbox.rate) || 80, d: 0, u: '/min', t: '<b>messages triaged</b>, 32 at a time', w: 70},
  ];
  const s8 = scene('s8', `<div class="col">
      ${kicker('', 'Benchmarks · this laptop')}
      ${headline('The <em>numbers.</em>')}
      <div class="metrics">${M.map(m => `<div class="metric" style="--w:0%"><div class="n" data-n="${m.n}" data-d="${m.d}" data-u="${m.u}">0</div><div class="d">${m.t}</div></div>`).join('')}</div>
    </div>`);
  hold(s8, T(B8), T(E8));
  titles(s8, T(B8));
  cue(T(B8), 'numbers:hit', 'impact');
  call(T(B8), () => { Die.heatAll(0.8); Die.pulseBurst(24, 1, 700); Die.telemetry(100, 0.7); });
  camTo(pick({ax: 0.84, ay: 0.5, fx: 0, fy: 0, zoom: 1.0, alpha: 0.9}, {ax: 0.5, ay: 0.2, fx: 0, fy: 0, zoom: 1.2, alpha: 0.9}), T(B8) - 0.5, 1.3);
  const ms = $$('.metric', s8);
  rise(ms, T(B8, 2), 0.09, 22);
  ms.forEach((m, i) => {
    const n = $('.n', m), t = T(B8, 2) + i * 0.09;
    count(n, +n.dataset.n, t, 1.1, +n.dataset.d, n.dataset.u);
    tl.to(m, {'--w': M[i].w + '%', duration: 1.3, ease: 'expo.out'}, t + 0.1);
  });

  /* ============================================================ outro */
  const B9 = 33.5;
  const s9 = scene('s9', `<div class="col">
      ${headline('Zero cloud calls.|<em>One laptop.</em>')}
      <div class="plate cmd"><span class="ps">PS&gt;</span>${pick(CMD, CMD2.replace('\n', '<br>'))}</div>
      <div class="repo">github.com/an6122003/rtx-spark-ai-workshop</div>
      <div class="byline"><img src="an.webp" alt=""><span><b>An À Ha</b> · @anndaynee<br><span>Engineer &amp; AI Product Builder · Tech &amp; AI Creator</span></span></div>
    </div>`);
  hold(s9, T(B9), END + 1);
  titles(s9, T(B9));
  call(T(B9), () => { Die.mark(null); Die.telemetry(20, 0.25); });
  camTo(pick({ax: 0.77, ay: 0.5, fx: 0, fy: 0, zoom: 1.3, alpha: 1}, {ax: 0.5, ay: 0.25, fx: 0, fy: 0, zoom: 1.6, alpha: 1}), T(B9) - 0.4, 1.5);
  rise($('.cmd', s9), T(B9, 2));
  rise($('.repo', s9), T(B9, 3), 0, 12);
  rise($('.byline', s9), T(B9 + 1));
  call(T(B9 + 1), () => { Die.heatAll(0.7); Die.pulseBurst(18, 1, 520); });
  cue(T(B9 + 1), 'outro:logo', 'note');
  tl.to(stage, {opacity: 0, duration: 0.9, ease: 'power2.in'}, END - 1.0);
  tl.to(cam, {alpha: 0, duration: 0.9, ease: 'power2.in'}, END - 1.0);

  /* ------------------------------------------------------------ driver --- */
  const total = Math.round(END * FPS);
  let last = -1;
  window.FILM = {
    fps: FPS, frames: total, duration: END, cues, downbeats: DB,
    frame(n) {   // frames come in order; one step of the chip per frame
      const t = n / FPS;
      VT.advanceTo(t);
      tl.time(t);
      Die.advance(last < 0 ? 0 : (n - last) / FPS);
      last = n;
      return t;
    },
  };
  $$('.swap').forEach(s => { s.style.position = 'relative'; s.style.height = pick('520px', '900px'); });
  $$('.part').forEach(p => { p.style.position = 'absolute'; p.style.left = 0; p.style.right = 0; p.style.top = 0; });
  FILM.frame(0);
})();
