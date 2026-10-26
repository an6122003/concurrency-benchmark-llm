/* NEON SPARK, prompt by prompt: an 18 s vertical cut (1080x1920) of the game Qwen3.8-27B wrote on the RTX Spark
 * laptop, from its one-shot through nine follow-up prompts to the final version.
 *
 *   evolution.html    render.ps1 -Format v -Base http://127.0.0.1:8777/evolution.html -Tag -evo
 *
 * The footage is the games themselves, captured frame by frame by bench/capture_game.py (comp/clips); every number
 * comes from evo-data.js (bench/make_evo_data.py: the report's iteration table). The score is the film's take cut
 * on its downbeats (EVO.score): the bar before its drop for five bars, then straight into its peak.
 *
 * The score, in this cut's time: the drop at 2.13 s, where the montage starts; bars of about 2 s, the cuts getting
 * quicker on its beats; its peak at 10 s, the final game; the end card at 16 s; a fade to 18 s.
 * The first frame is the cover: prompt 1 above prompt 10, the question already on screen.
 */
(function () {
  'use strict';
  document.body.classList.add('v', 'evo');
  const E = window.EVO, C = window.CLIPS || {};
  const FPS = 30, END = E.end || 18;
  const DB = E.downbeats;
  const B = (bar, beat) => DB[bar] + (beat || 0) * (DB[bar + 1] - DB[bar]) / 4;   // a time on the score's bars
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const fmt = (n, d) => Number(n).toLocaleString('en-US', {minimumFractionDigits: d || 0, maximumFractionDigits: d || 0});
  const pad = (n) => String(n).padStart(2, '0');
  const hm = (min) => `${Math.floor(min / 60)} h ${Math.round(min % 60)} min`;
  const tl = gsap.timeline({paused: true});
  const cues = [];   // what the sound design hangs on: {t, id, kind}
  const cue = (t, id, kind) => cues.push({t: +t.toFixed(3), id, kind});
  const R = E.rounds;
  const cum = R.map((r, i) => R.slice(0, i + 1).reduce((a, x) => a + x.minutes, 0));

  /* ------------------------------------------------------------- what plays when --- */
  const SEG = [   // one cut a prompt, quicker as the score climbs to its peak
    {clip: 'p01', from: 64, t0: B(1), t1: B(2), cap: 'Gorgeous. But it <em>skips every wave.</em>'},
    {clip: 'p02', from: 2, t0: B(2), t1: B(2, 2), cap: 'Waves fixed.'},
    {clip: 'p03', from: 2, t0: B(2, 2), t1: B(3), cap: 'Story, sectors, bosses.'},
    {clip: 'p04', from: 2, t0: B(3), t1: B(3, 2), cap: 'New sectors. <em>HUD broke.</em>'},
    {clip: 'p05', from: 2, t0: B(3, 2), t1: B(3, 3), cap: 'HUD is back.'},
    {clip: 'p06', from: 2, t0: B(3, 3), t1: B(4), cap: 'Bosses break apart.'},
    {clip: 'p07', from: 2, t0: B(4), t1: B(4, 1), cap: 'Free flight.'},
    {clip: 'p08', from: 2, t0: B(4, 1), t1: B(4, 2), cap: 'Phone layout.', phone: true},
    {clip: 'p09', from: 2, t0: B(4, 2), t1: B(4, 3), cap: 'Zero errors.', phone: true},
    {clip: 'p10', from: 2, t0: B(4, 3), t1: B(5), cap: 'Polished.', phone: true},
  ];
  const FIN = [   // the final game on the peak
    {clip: 'f1', from: 0, t0: B(5), t1: B(5, 3), cap: 'Three sectors.'},
    {clip: 'f2', from: 0, t0: B(5, 3), t1: B(6, 2), cap: 'Overdrive.'},
    {clip: 'f3', from: 0, t0: B(6, 2), t1: B(7, 1), cap: 'Boss fights.'},
    {clip: 'f3', from: 48, t0: B(7, 1), t1: B(8), cap: 'Last words.'},
  ];

  /* ------------------------------------------------------------------ the page --- */
  $('#stage').innerHTML = `
    <div id="cover">
      <div class="kicker"><span>NEON SPARK · built by a local AI</span><i class="rule"></i></div>
      <h1 class="h1"><span class="ln"><span class="li">Same local AI.</span></span><span class="ln"><span class="li"><em>${R.length} prompts.</em></span></span></h1>
    </div>
    <div id="top">
      <div class="kick"><div class="k1">NEON SPARK · built by a local AI<i class="rule"></i></div><div class="k2">Prompt ${R.length} · the final game<i class="rule"></i></div></div>
      <div class="pno"><span class="lab">PROMPT</span><div class="nums">${R.map((r) => `<span class="num">${pad(r.n)}</span>`).join('')}</div><span class="of">/ ${pad(R.length)}</span></div>
      <div class="caps">${SEG.concat(FIN).map((s) => `<div class="cap">${s.cap}</div>`).join('')}</div>
    </div>
    <div id="band">
      <div class="media"><img class="desk" alt=""><div class="stagebg"></div><div class="phone"><img alt=""></div></div>
      <div id="flash"></div>
      <div class="tag tagA">PROMPT <b>1</b></div>
    </div>
    <div id="bandB"><img alt=""><div class="tag">PROMPT <b>${R.length}</b></div></div>
    <div id="rail">
      <div class="segs">${R.map(() => '<div class="seg"><i></i></div>').join('')}</div>
      <div class="stats">
        <div class="stat"><div class="k">Lines of code</div><div class="v lines">0</div></div>
        <div class="stat"><div class="k">Minutes of generation</div><div class="v mins">0</div></div>
        <div class="stat hand"><div class="k">Written by hand</div><div class="v">0</div></div>
      </div>
      <div class="model"><b>Qwen3.8-27B</b> · offline on an RTX Spark laptop</div>
    </div>
    <section id="end"><div class="col">
      <div class="kicker"><span>NEON SPARK · built by a local AI</span><i class="rule"></i></div>
      <h1 class="h1"><span class="ln"><span class="li">${R.length} prompts.</span></span><span class="ln"><span class="li"><em>0 lines by hand.</em></span></span></h1>
      <p class="lead">Qwen3.8-27B wrote all <b>${fmt(E.final_lines)} lines</b> in <b>${hm(E.total_minutes)}</b> of generation, offline on an RTX Spark laptop.</p>
      <div class="byline"><img src="an.webp" alt=""><span><b>An À Ha</b> · @anndaynee<br>Engineer &amp; AI Product Builder · Tech &amp; AI Creator</span></div>
    </div></section>`;

  const desk = $('#band img.desk'), phoneImg = $('#band .phone img'), imgB = $('#bandB img');
  const nums = $$('.pno .num'), caps = $$('.caps .cap'), segs = $$('.seg i');
  const linesEl = $('.stat .lines'), minsEl = $('.stat .mins');
  function count(el, from, to, t, dur) {
    const o = {v: from};
    tl.fromTo(o, {v: from}, {v: to, duration: dur, ease: 'power3.out', onUpdate: () => { el.textContent = fmt(o.v); }}, t);
  }
  function flip(list, i, t) {   // the one before goes up and out, this one comes up in
    if (i > 0) tl.to(list[i - 1], {yPercent: -70, opacity: 0, duration: 0.14, ease: 'power2.in'}, t);
    tl.fromTo(list[i], {yPercent: 70, opacity: 0}, {yPercent: 0, opacity: 1, duration: 0.22, ease: 'expo.out'}, t);
  }
  function cut(t, big) {   // a flash and a punch on every cut (not drawn before it: no immediate render)
    tl.fromTo('#flash', {opacity: big ? 0.85 : 0.45},
      {opacity: 0, duration: big ? 0.35 : 0.16, ease: 'power2.out', immediateRender: false}, t);
    tl.fromTo('#band .media', {scale: big ? 1.12 : 1.05},
      {scale: 1, duration: big ? 0.6 : 0.32, ease: 'expo.out', immediateRender: false}, t);
  }
  function screen(phone, t) {   // the game full width, or a phone in the middle of the screen
    tl.set(desk, {opacity: phone ? 0 : 1}, t);
    tl.set('#band .stagebg', {opacity: phone ? 1 : 0}, t);
    tl.set('#band .phone', {opacity: phone ? 1 : 0}, t);
  }

  /* ================================================================ the cover --- */
  // set now, not on the timeline: a paused timeline does not draw its time-0 state when it is sought to 0
  gsap.set('#band', {left: 140, top: 560, width: 800, height: 450, borderRadius: 20});
  gsap.set(nums, {opacity: 0});
  gsap.set('#top .k2', {opacity: 0});
  gsap.set('#band .stagebg, #band .phone', {opacity: 0});

  /* ======================================================= the drop: prompt 1 --- */
  tl.to('#cover', {opacity: 0, y: -40, duration: 0.25, ease: 'power2.in'}, B(1) - 0.22);
  tl.to('#bandB', {y: 520, opacity: 0, duration: 0.42, ease: 'power3.in'}, B(1) - 0.3);
  tl.to('.tagA', {opacity: 0, duration: 0.2, ease: 'power2.in'}, B(1) - 0.12);
  tl.to('#band', {left: 0, top: 640, width: 1080, height: 608, borderRadius: 0, duration: 0.55, ease: 'expo.inOut'}, B(1) - 0.2);
  tl.set('#top', {opacity: 1}, B(1));
  tl.from('#top .k1', {opacity: 0, letterSpacing: '0.55em', duration: 0.7, ease: 'expo.out'}, B(1));
  tl.fromTo('#rail', {opacity: 0, y: 40}, {opacity: 1, y: 0, duration: 0.6, ease: 'expo.out'}, B(1) + 0.1);
  cue(B(1), 'drop', 'impact');

  /* ====================================================== one cut a prompt --- */
  SEG.forEach((s, i) => {
    flip(nums, i, s.t0);
    flip(caps, i, s.t0);
    screen(!!s.phone, s.t0);
    tl.to(segs[i], {scaleX: 1, duration: 0.3, ease: 'expo.out'}, s.t0);
    count(linesEl, i ? R[i - 1].lines : 0, R[i].lines, s.t0, i ? 0.3 : 0.9);
    count(minsEl, i ? cum[i - 1] : 0, cum[i], s.t0, i ? 0.3 : 0.9);
    if (i) {
      cut(s.t0, false);
      cue(s.t0, `prompt:${i + 1}`, i < 4 ? 'whoosh' : 'tick');
    }
  });

  /* ======================================================== the final game --- */
  tl.to('#top .k1', {opacity: 0, duration: 0.15, ease: 'power2.in'}, B(5));
  tl.fromTo('#top .k2', {opacity: 0, letterSpacing: '0.55em'}, {opacity: 1, letterSpacing: '0.3em', duration: 0.7, ease: 'expo.out'}, B(5));
  FIN.forEach((s, j) => {
    const i = SEG.length + j;
    flip(caps, i, s.t0);
    screen(false, s.t0);
    cut(s.t0, j === 0);
    cue(s.t0, j ? `final:${j}` : 'peak', j ? 'whoosh' : 'impact');
  });

  /* ================================================================== the end --- */
  const end = $('#end');
  tl.to(end, {opacity: 1, duration: 0.3, ease: 'power2.out'}, B(8));
  tl.from($$('.h1 .li', end), {yPercent: 118, duration: 0.65, ease: 'expo.out', stagger: 0.08}, B(8) + 0.05);
  tl.from($('.kicker', end), {opacity: 0, letterSpacing: '0.55em', duration: 0.7, ease: 'expo.out'}, B(8));
  tl.from($('.lead', end), {opacity: 0, y: 28, duration: 0.55, ease: 'expo.out'}, B(8) + 0.35);
  tl.from($('.byline', end), {opacity: 0, y: 28, duration: 0.55, ease: 'expo.out'}, B(8) + 0.6);
  cue(B(8), 'end', 'chime');

  /* ------------------------------------------------------------------- footage --- */
  const SHOTS = [
    {img: desk, clip: 'p01', from: 0, t0: 0, t1: B(1)},                       // the cover: prompt 1 on top ...
    {img: imgB, clip: 'f3', from: 48, t0: 0, t1: B(1) + 0.5, speed: 0.75},    // ... and the final game below
    ...SEG.map((s) => ({img: s.phone ? phoneImg : desk, clip: s.clip, from: s.from, t0: s.t0, t1: s.t1})),
    ...FIN.map((s) => ({img: desk, clip: s.clip, from: s.from, t0: s.t0, t1: s.t1})),
  ];

  /* -------------------------------------------------------------------- driver --- */
  window.FILM = {
    fps: FPS, frames: Math.round(END * FPS), duration: END, cues, downbeats: DB, score: E.score,
    frame(n) {   // seek the timeline, then show each visible screen's frame of its clip once it has decoded
      const t = n / FPS;
      VT.advanceTo(t);
      tl.time(t);
      const loads = [];
      for (const s of SHOTS) {
        const c = C[s.clip];
        if (!c || t < s.t0 || t >= s.t1) continue;
        const idx = Math.min(c.frames - 1, s.from + Math.floor((t - s.t0) * FPS * (s.speed || 1) + 1e-6));
        const src = `clips/${s.clip}/${String(idx).padStart(5, '0')}.jpg`;
        if (s.img.getAttribute('src') !== src) s.img.setAttribute('src', src);
        loads.push(s.img.decode().catch(() => null));
      }
      return Promise.all(loads).then(() => t);
    },
  };
  FILM.frame(0);
})();
