/* NEON SPARK, the arcade cut: a 19 s vertical film (1080x1920) told inside the game's own world: its footage, its type,
 * its neon, its music and its sound effects. The game Qwen3.8-27B wrote on the RTX Spark laptop, prompt by prompt,
 * then the finished game, then what the build took. No byline: the game's victory screen closes it.
 *
 *   arcade.html    render.ps1 -Format v -Base http://127.0.0.1:8777/arcade.html -Tag -arcade
 *
 * The footage is the games themselves, captured in portrait (bench/capture_game.py bench/arcade-clips.json, into
 * comp/clips/a-*). The sound is the game's own synth rendered offline (arcade-score.js, arcade-audio.html,
 * bench/render_arcade_audio.py, audio/master_arcade.py); every cut here lands on its eighth-note grid (SCORE.T), and
 * hits as hard as the game's effect on it. Every number comes from arcade-data.js (bench/make_arcade_data.py).
 *
 *   0 s       the cover: the title over the game's intro transmission, typed on the score's blips
 *   1.9 s     a big boom: prompt 1. A cut a prompt; the colour and the tempo change sector at prompts 4 and 7
 *   11.4 s    the boss track: a boss-wave banner, the final game in four shots
 *   15.6 s    the boss's death boom: the victory screen, what the build took, a line a blip
 * Only the entrances are tweened (GSAP); everything else is drawn from the time alone, so any frame renders on its own.
 */
(function () {
  'use strict';
  const S = window.SCORE, A = window.ARC, C = window.CLIPS || {};
  const R = A.rounds, TOT = A.totals, MOD = A.model;
  const FPS = 30, END = S.end, T = S.T, OUT = S.outro, ST = S.stats;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const fmt = (n) => Math.round(n).toLocaleString('en-US');
  const pad = (n, k) => String(n).padStart(k || 2, '0');
  const kTok = (n) => Math.round(n / 1024);   // context in K of 1,024 tokens, as llama.cpp sizes its windows (96K = 98,304)
  const hm = (min) => {   // 12m, 1h 03m
    const m = Math.round(min);
    return m < 60 ? `${m}<small>m</small>` : `${Math.floor(m / 60)}<small>h</small> ${pad(m % 60)}<small>m</small>`;
  };
  const ease = (x) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);   // the game's easeOutCubic
  const hash = (a, b) => {   // a fixed random number in [0, 1) for a frame and a channel: the glitches render the same every time
    let h = Math.imul((a + 0x9e3779b9) | 0, 0x85ebca6b) ^ Math.imul((b + 0x632be5ab) | 0, 0xc2b2ae35);
    h ^= h >>> 16; h = Math.imul(h, 0x7feb352d); h ^= h >>> 15; h = Math.imul(h, 0x846ca68b); h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
  const ACC = {s1: '#ff2d95', s2: '#00e5ff', s3: '#ff8a00', boss: '#ff8a00'};   // the game's sectors' accents
  const NEON = ['#ff2d95', '#00e5ff', '#76b900'];   // the glow its victory title cycles through
  const sectionAt = (t) => S.sections.filter((s) => t >= s.t0 - 1e-6).pop().id;

  /* ------------------------------------------------------------- what plays when --- */
  const CAPS = ['Gorgeous. Skips every wave.', 'Waves fixed.', 'Story. Sectors. Bosses.', 'New sectors. HUD broke.',
    'HUD restored.', 'Bosses break apart.', 'Free flight.', 'Fits any screen.', 'Zero errors.', 'Polished.'];
  const SHOTS = [
    {id: 'IN', clip: 'a-bg1', t0: 0},   // the transmission, over the game's sky before the first wave
    ...R.map((r, i) => ({id: `P${r.n}`, clip: `a-p${pad(r.n)}`, t0: T[`P${r.n}`], cap: CAPS[i], prompt: i})),
    {id: 'F1', clip: 'a-f1', t0: T.F1, cap: 'Three sectors.'},   // the final game, on the boss track
    {id: 'F2', clip: 'a-f2', t0: T.F2, cap: 'Overdrive.'},
    {id: 'F3', clip: 'a-f3', t0: T.F3, cap: 'Boss fights.'},
    {id: 'F4', clip: 'a-f3', t0: T.F4, from: 36, cap: 'Last words.'},
    {id: 'OUT', clip: 'a-bg3', t0: OUT},   // the victory screen, over the Core's sky
  ];
  SHOTS.forEach((s, i) => { s.from = s.from || 0; s.t1 = SHOTS[i + 1] ? SHOTS[i + 1].t0 : Infinity; });
  const shotAt = (t) => SHOTS.filter((s) => t >= s.t0 - 1e-6).pop();
  const frameOf = (s, t) => {
    const k = Math.min(C[s.clip].frames - 1, s.from + Math.max(0, Math.floor((t - s.t0) * FPS + 1e-6)));
    return `clips/${s.clip}/${pad(k, 5)}.jpg`;
  };

  // how hard each cut hits: as hard as the game's own effect on it (SCORE.sfx)
  const KIND = {
    big: {amp: 1, dur: 0.5, white: 0.95, tau: 0.09, shake: 26, tint: 0.45, slide: 150},     // sfxBoom(true)
    mid: {amp: 0.8, dur: 0.3, white: 0.5, tau: 0.06, shake: 12, tint: 0.3, slide: 110},     // sfxBoom(false)
    small: {amp: 0.55, dur: 0.17, white: 0.24, tau: 0.045, shake: 4, tint: 0, slide: 80},  // sfxLaser
  };
  const HIT = {P1: 'big', P4: 'mid', P7: 'mid', F1: 'big', F2: 'mid', F3: 'mid', F4: 'mid', OUT: 'big'};
  const CUTS = SHOTS.slice(1).map((s, i) => ({id: s.id, t: s.t0, kind: HIT[s.id] || 'small',
    pre: s.id === 'P1' || s.id === 'F1',   // the game's rising sfxOver sweep runs into these: the screen frays first
    prev: frameOf(SHOTS[i], s.t0 - 0.5 / FPS)}));
  const cues = CUTS.map((c) => ({t: c.t, id: c.id, kind: c.kind}))
    .concat(Array.from({length: ST.n}, (_, i) => ({t: +(ST.t0 + i * ST.gap).toFixed(3), id: `stat:${i + 1}`, kind: 'blip'})));

  /* ------------------------------------------------------------------ the page --- */
  const ROWS = [   // the victory screen's tally: what the build took
    ['MODEL', `${MOD.name} <small>${MOD.quant}</small>`],
    ['RUNS ON', MOD.hardware],
    ['PROMPTS', String(TOT.prompts)],
    ['TOKENS GENERATED', fmt(TOT.tokens_out)],
    ['TOKENS READ', fmt(TOT.tokens_in)],
    ['PEAK CONTEXT', `${kTok(TOT.peak_context)}K <small>/ ${kTok(TOT.peak_window)}K</small>`],
    ['GENERATION TIME', `${Math.floor(Math.round(TOT.minutes) / 60)} <small>h</small> ${Math.round(TOT.minutes) % 60} <small>min</small>`],
    ['AVG SPEED', `${Math.round(TOT.tps)} <small>tok/s</small>`],
    ['LINES OF CODE', fmt(TOT.lines)],
    ['WRITTEN BY HAND', '0', 'hand'],
  ];
  $('#world').innerHTML = `
    <div id="cam">
      <img id="shot" alt="">
      <div id="split"><img class="r" alt=""><img class="gb" alt=""></div>
      <div id="slices">${'<div><img alt=""></div>'.repeat(8)}</div>
    </div>
    <div id="bars">${'<i></i>'.repeat(10)}</div>
    <div id="tint"></div>
    <div id="dim"></div>
    <div id="floor"></div>
    <section id="intro">
      <div class="logo">NEON SPARK</div>
      <div class="tag">S Y N T H W A V E   A R C A D E</div>
      <div class="hdr">▸▸ INCOMING TRANSMISSION ◄◄</div>
      <i class="rule"></i>
      <div class="lines">${S.intro.lines.map(() => '<span class="line"><span class="tx"></span></span>').join('')}</div>
      <i class="cur"></i>
      <div class="go">PRESS START ▸</div>
    </section>
    <div id="banner"><span>⚠︎ FINAL BUILD ⚠︎</span></div>
    <section id="hud">
      <div class="cap"><span></span></div>
      <div class="row">
        <div class="pno"><span class="lab">PROMPT</span><span class="num">01</span><span class="of">/${R.length}</span></div>
        <div class="build"><div class="who"><b>${MOD.name}</b> · ${MOD.hardware}</div><div class="bar">${'<i></i>'.repeat(R.length)}</div></div>
      </div>
      <div class="stats">
        <div class="stat tok"><div class="k">TOKENS</div><div class="v"></div><div class="pop"></div></div>
        <div class="stat ctx"><div class="k">CONTEXT</div><div class="v"></div></div>
        <div class="stat time"><div class="k">TIME</div><div class="v"></div></div>
        <div class="stat lines"><div class="k">LINES</div><div class="v"></div></div>
      </div>
    </section>
    <section id="end">
      <div class="title"><span>BUILD COMPLETE</span></div>
      <div class="sub">NEON SPARK · coded offline by a local AI</div>
      <div class="table">${ROWS.map(([k, v, cls]) => `<div class="row${cls ? ` ${cls}` : ''}"><span class="k">${k}</span><span class="v">${v}</span></div>`).join('')}</div>
      <div class="btn">PLAY AGAIN</div>
    </section>
    <div id="white"></div>`;

  const set = (el, text) => { if (el.textContent !== text) el.textContent = text; };
  const html = (el, h) => { if (el.innerHTML !== h) el.innerHTML = h; };

  /* ----------------------------------------------- the transmission (the cover) --- */
  const IN = S.intro, lines = $$('#intro .line .tx'), cur = $('#intro .cur'), go = $('#intro .go'), hdr = $('#intro .hdr');
  const typedAt = (t) => {   // characters up on each line: the first is up on the cover, the others type on the blips
    let k = 0;
    return IN.lines.map((line, li) => {
      if (!li) return line.length;
      let c = 0;
      for (let i = 0; i < line.length; i++, k++) if (t >= IN.t0 + (li - 1) * 0.18 + k / IN.rate - 1e-6) c = i + 1;
      return c;
    });
  };
  const typing = [IN.typing[0], IN.typing[IN.typing.length - 1]];
  function drawIntro(t, n) {
    if (t >= T.P1) return;
    let at = 0;
    typedAt(t).forEach((c, i) => { set(lines[i], IN.lines[i].slice(0, c)); if (c) at = i; });
    if (cur.parentNode !== lines[at].parentNode) lines[at].parentNode.appendChild(cur);
    const steady = t >= typing[0] - 0.05 && t <= typing[1] + 0.1;   // solid while it types, the game's 1.5 Hz blink otherwise
    cur.style.visibility = steady || Math.floor(t * 3) % 2 === 0 ? 'visible' : 'hidden';
    const d = ease((t - typing[1] - 0.08) / 0.25);
    go.style.opacity = t > typing[1] ? (d * (0.45 + 0.55 * Math.abs(Math.cos((t - typing[1]) * 7)))).toFixed(3) : 0;
    hdr.style.transform = hash(n, 6) < 0.15 ? `translateX(${((hash(n, 7) - 0.5) * 8).toFixed(1)}px)` : '';   // its header's jitter
  }

  /* ------------------------------------------------------------- the build HUD --- */
  const hud = $('#hud'), cap = $('#hud .cap span'), num = $('#hud .num'), bar = $('#hud .bar'), segs = $$('#hud .bar i');
  const vTok = $('#hud .tok .v'), vCtx = $('#hud .ctx .v'), vTime = $('#hud .time .v'), vLines = $('#hud .lines .v');
  const pop = $('#hud .pop'), floor = $('#floor');
  const cumTok = [], cumMin = [];   // what the build has taken so far, prompt by prompt
  R.forEach((r, i) => { cumTok[i] = (i ? cumTok[i - 1] : 0) + r.tokens_out; cumMin[i] = (i ? cumMin[i - 1] : 0) + r.minutes; });
  function drawHud(t, s) {
    if (t < T.P1 || t >= OUT) return;
    let i = 0;
    for (let j = 1; j < R.length; j++) if (t >= T[`P${j + 1}`] - 1e-6) i = j;
    const t0 = T[`P${i + 1}`], x = ease((t - t0) / (i ? 0.45 : 0.9));   // the numbers count up, like the game's score
    const from = (a, b) => (i ? a : 0) + ((b - (i ? a : 0)) * x);
    hud.style.setProperty('--acc', ACC[sectionAt(t)]);
    floor.classList.toggle('solid', s.id === 'P9' || s.id === 'P10');   // the upgrade cards would show through the HUD
    set(cap, s.cap);
    set(num, pad(i + 1));
    set(vTok, fmt(from(cumTok[i - 1], cumTok[i])));
    html(vCtx, `${Math.round(from(kTok((R[i - 1] || R[0]).context), kTok(R[i].context)))}K<small>/${kTok(R[i].window)}K</small>`);
    html(vTime, hm(from(cumMin[i - 1], cumMin[i])));
    set(vLines, fmt(from((R[i - 1] || R[0]).lines, R[i].lines)));
    set(pop, `+${fmt(R[i].tokens_out)}`);
    segs.forEach((g, k) => { g.className = k < i ? 'on' : k > i ? '' : t - t0 < 0.2 ? 'new' : 'on'; });
    bar.style.opacity = t >= T.F1 ? (0.7 + 0.3 * Math.abs(Math.sin(t * 6))).toFixed(3) : '';   // full: the game's READY pulse
  }

  /* ---------------------------------------------------------- the victory screen --- */
  const title = $('#end .title span'), btn = $('#end .btn');
  function drawEnd(t, n) {
    if (t < OUT) return;
    const col = NEON[Math.floor(t * 4) % 3];   // the game's title glow: pink, cyan, green, four times a second
    title.style.textShadow = `0 0 6px #fff, 0 0 26px ${col}, 0 0 70px ${col}`;
    title.style.transform = t > OUT + 0.8 && hash(n, 8) < 0.1 ? `translateX(${((hash(n, 9) - 0.5) * 14).toFixed(1)}px)` : '';
    const p = 0.5 + 0.5 * Math.abs(Math.sin((t - OUT) * 2.6));
    btn.style.boxShadow = `0 0 ${Math.round(14 + 30 * p)}px rgba(118, 185, 0, ${(0.45 + 0.55 * p).toFixed(2)})`;
  }

  /* ---------------------------------------------------------------- the glitch --- */
  const cam = $('#cam'), shot = $('#shot'), split = $('#split'), [red, gb] = $$('#split img');
  const slicesBox = $('#slices'), slices = $$('#slices div'), sliceImgs = $$('#slices img');
  const bars = $$('#bars i'), tint = $('#tint'), white = $('#white');
  const show = (img, src, loads) => {
    if (img.getAttribute('src') !== src) img.setAttribute('src', src);
    loads.push(img.decode().catch(() => null));
  };
  function glitch(t, n, src, loads) {
    let g = null;
    for (const c of CUTS) {   // the strongest cut in reach: one just made, or one the sweep is running into
      const k = KIND[c.kind], dt = t - c.t;
      let v = 0;
      if (dt >= -1e-6 && dt < k.dur) v = k.amp * Math.pow(1 - dt / k.dur, 1.5);
      else if (c.pre && dt < 0 && dt > -0.5) v = 0.34 * Math.pow(1 + dt / 0.5, 2);
      if (v > (g ? g.v : 0)) g = {c, k, dt, v, pre: dt < 0};
    }
    const v = g ? g.v : 0, r = (k) => hash(n, k), hit = g && !g.pre;
    white.style.opacity = hit ? (g.k.white * Math.exp(-g.dt / g.k.tau)).toFixed(3) : 0;
    tint.style.opacity = g ? (v * (hit ? g.k.tint : 0.3)).toFixed(3) : 0;
    // the colours tear apart: red one way, green and blue the other
    if (v > 0.02) {
      const dx = v * (14 + 18 * r(1)), dy = (r(2) - 0.5) * v * 10;
      split.style.opacity = 1;
      red.style.transform = `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px)`;
      gb.style.transform = `translate(${(-dx).toFixed(1)}px, ${(-dy).toFixed(1)}px)`;
      show(red, src, loads);
      show(gb, src, loads);
    } else split.style.opacity = 0;
    // bands of the picture slide sideways; for the cut's first frames half of them still show the shot before it
    if (hit && v > 0.12) {
      slicesBox.style.opacity = 1;
      slices.forEach((d, i) => {
        if (r(10 + i) > 0.7) { d.style.display = 'none'; return; }
        const y = Math.floor(r(20 + i) * 1800), h = Math.floor(16 + r(30 + i) * 150);
        d.style.display = 'block';
        d.style.top = `${y}px`;
        d.style.height = `${h}px`;
        d.style.transform = `translateX(${((r(40 + i) - 0.5) * 2 * v * g.k.slide).toFixed(1)}px)`;
        sliceImgs[i].style.top = `${-y}px`;
        show(sliceImgs[i], g.dt < 2.5 / FPS && i % 2 === 0 ? g.c.prev : src, loads);
      });
    } else slicesBox.style.opacity = 0;
    // scan bars: on a cut, or now and then while the transmission comes in (the game's 15%)
    const idle = !g && t < T.P1 && r(5) < 0.15;
    const nb = g ? Math.max(1, Math.round(v * bars.length)) : idle ? 2 : 0;
    bars.forEach((b, i) => {
      if (i >= nb) { b.style.opacity = 0; return; }
      b.style.top = `${Math.floor(r(60 + i) * 1912)}px`;
      b.style.height = `${Math.round(3 + r(70 + i) * 10)}px`;
      b.style.background = idle ? (i ? '#ff2d95' : '#00e5ff') : ['#00e5ff', '#ff2d95', '#ffffff'][Math.floor(r(80 + i) * 3)];
      b.style.opacity = idle ? 0.3 : ((0.3 + 0.7 * r(90 + i)) * Math.min(1, v * 1.6)).toFixed(3);
    });
    // the screen shakes on a hit, zoomed in enough that its edges never show
    if (hit && g.k.shake) {
      const a = v * g.k.shake;
      cam.style.transform = `translate(${((r(3) - 0.5) * 2 * a).toFixed(1)}px, ${((r(4) - 0.5) * 1.2 * a).toFixed(1)}px) scale(${(1 + 0.07 * v).toFixed(4)})`;
    } else cam.style.transform = '';
  }

  /* --------------------------------------------------------------- the entrances --- */
  const tl = gsap.timeline({paused: true});
  // the cover: set now, not on the timeline (a paused timeline does not draw its time-0 state when sought to 0)
  gsap.set('#dim', {opacity: 0.6});   // the game's intro dims its sky
  // prompt 1, on the big boom
  tl.set('#intro', {opacity: 0}, T.P1);
  tl.set('#dim', {opacity: 0}, T.P1);
  tl.fromTo('#floor', {opacity: 0}, {opacity: 1, duration: 0.35, ease: 'power2.out', immediateRender: false}, T.P1);
  tl.fromTo('#hud', {opacity: 0, y: 80}, {opacity: 1, y: 0, duration: 0.55, ease: 'expo.out', immediateRender: false}, T.P1 + 0.03);
  // every cut: the caption pops in like the game's wave name; a prompt's number punches, what it generated pops up
  SHOTS.filter((s) => s.cap).forEach((s) => tl.fromTo('#hud .cap span', {opacity: 0, scale: 0.86},
    {opacity: 1, scale: 1, duration: 0.22, ease: 'back.out(2.2)', immediateRender: false}, s.t0));
  SHOTS.filter((s) => s.prompt !== undefined).forEach((s) => {
    tl.fromTo('#hud .num', {scale: 1.45}, {scale: 1, duration: 0.32, ease: 'back.out(2.4)', immediateRender: false}, s.t0);
    tl.fromTo(pop, {opacity: 1, y: 0}, {opacity: 0, y: -70, duration: 0.7, ease: 'power2.out', immediateRender: false}, s.t0 + 0.04);
  });
  // the final game: a boss-wave banner
  tl.fromTo('#banner', {opacity: 0, scale: 0.88}, {opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(2.4)', immediateRender: false}, T.F1);
  tl.to('#banner', {opacity: 0, duration: 0.2, ease: 'power2.in'}, T.F2 - 0.22);
  // the victory screen: the title, the story line, a row a blip, then the button on the power-up
  tl.set('#hud, #floor', {opacity: 0}, OUT);
  tl.fromTo('#dim', {opacity: 0}, {opacity: 0.74, duration: 0.5, ease: 'power1.out', immediateRender: false}, OUT);
  tl.set('#end', {opacity: 1}, OUT);
  tl.fromTo('#end .title', {opacity: 0, scale: 0.78}, {opacity: 1, scale: 1, duration: 0.55, ease: 'back.out(1.8)', immediateRender: false}, OUT + 0.1);
  tl.fromTo('#end .sub', {opacity: 0, y: 18}, {opacity: 1, y: 0, duration: 0.45, ease: 'expo.out', immediateRender: false}, OUT + 0.42);
  $$('#end .row').forEach((row, i) => tl.fromTo(row, {opacity: 0, x: -28},
    {opacity: 1, x: 0, duration: 0.2, ease: 'power3.out', immediateRender: false}, ST.t0 + i * ST.gap));
  tl.fromTo(btn, {opacity: 0, scale: 0.86}, {opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2.2)', immediateRender: false},
    ST.t0 + ST.n * ST.gap + 0.1);

  /* -------------------------------------------------------------------- driver --- */
  window.FILM = {
    fps: FPS, frames: Math.round(END * FPS), duration: END, cues, downbeats: null, score: null,
    frame(n) {   // seek the timeline, draw the frame's state, then wait until every picture on screen has decoded
      const t = n / FPS, loads = [];
      VT.advanceTo(t);
      tl.time(t);
      const s = shotAt(t), src = frameOf(s, t);
      show(shot, src, loads);
      drawIntro(t, n);
      drawHud(t, s);
      drawEnd(t, n);
      glitch(t, n, src, loads);
      return Promise.all(loads).then(() => t);
    },
  };
  FILM.frame(0);
})();
