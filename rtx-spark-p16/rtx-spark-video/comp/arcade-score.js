/* The arcade cut's score: NEON SPARK's own music, track by track, quicker with every sector, and the game's own
 * sound effects on the cuts. arcade-audio.html renders it (with the game's synth, game-audio.js); arcade.js cuts
 * on the same times. The game steps its music in eighth notes; every time here is on that grid.
 *
 *   intro + prompts 1-3   sector 1 track, 128 BPM      prompts 4-6   sector 2, 140 BPM
 *   prompts 7-10          sector 3, 152 BPM            the final game   the boss track, 168 BPM
 *   the stats             no music: the boss's death boom, the sector-clear chime, a blip a line (the game's victory)
 * Three stop-downs: the music drops out under the game's rising sweep into prompt 1 and into the final build, and
 * under the boss's last words before its death boom.
 */
(function () {
  'use strict';
  const TEMPO = {s1: 128, s2: 140, s3: 152, boss: 168};
  const OUTRO = 3.6;
  const spb = (bpm) => 60 / bpm / 2;
  const sections = [];
  let t = 0;
  for (const [id, track, steps] of [['s1', 0, 24], ['s2', 1, 12], ['s3', 2, 16], ['boss', 'boss', 24]]) {
    sections.push({id, track, steps, t0: t, spb: spb(TEMPO[id])});
    t += steps * spb(TEMPO[id]);
  }
  const outro = t;
  const at = (id, step) => { const s = sections.find((x) => x.id === id); return s.t0 + step * s.spb; };
  const cuts = [   // where each shot starts: [id, section, step]
    ['P1', 's1', 8], ['P2', 's1', 16], ['P3', 's1', 20],
    ['P4', 's2', 0], ['P5', 's2', 4], ['P6', 's2', 8],
    ['P7', 's3', 0], ['P8', 's3', 4], ['P9', 's3', 8], ['P10', 's3', 12],
    ['F1', 'boss', 0], ['F2', 'boss', 6], ['F3', 'boss', 12], ['F4', 'boss', 18],
  ].map(([id, sec, step]) => ({id, t: +at(sec, step).toFixed(4)}));
  const T = Object.fromEntries(cuts.map((c) => [c.id, c.t]));
  const rests = [['s1', 6, 8], ['boss', 22, 24], ['s3', 14, 16]]   // [section, first silent step, the step it ends at)
    .map(([id, from, to]) => ({id, from, to, t0: +at(id, from).toFixed(4), t1: +at(id, to).toFixed(4)}));

  // the transmission types itself, a blip a character (the first line is already up on the cover)
  const INTRO_LINES = ['ONE LOCAL AI.', 'TEN PROMPTS.', 'ONE GAME.'];
  const typing = [];
  let k = 0;
  const rate = 26, t0 = 0.22;   // characters a second
  INTRO_LINES.slice(1).forEach((line, li) => {
    for (let i = 0; i < line.length; i++) {
      const tc = t0 + li * 0.18 + (k++) / rate;
      if (line[i] !== ' ') typing.push(+tc.toFixed(4));
    }
  });
  const STAT_T0 = outro + 0.75, STAT_GAP = 0.16, STATS = 10;
  const sfx = [];   // [time, game function, its argument]
  typing.forEach((tt) => sfx.push([tt, 'sfxBlip']));
  sfx.push([T.P1 - 0.5, 'sfxOver'], [T.P1, 'sfxBoom', true]);
  for (const id of ['P2', 'P3', 'P5', 'P6', 'P8', 'P9', 'P10']) sfx.push([T[id], 'sfxLaser']);
  for (const id of ['P4', 'P7']) sfx.push([T[id], 'sfxBoom', false], [T[id], 'sfxShield']);
  sfx.push([T.F1 - 0.5, 'sfxOver'], [T.F1, 'sfxBoom', true]);
  for (const id of ['F2', 'F3', 'F4']) sfx.push([T[id], 'sfxBoom', false]);
  sfx.push([outro, 'sfxBoom', true], [outro + 0.3, 'sfxClear']);
  for (let i = 0; i < STATS; i++) sfx.push([STAT_T0 + i * STAT_GAP, 'sfxBlip']);
  sfx.push([STAT_T0 + STATS * STAT_GAP + 0.1, 'sfxPower']);
  sfx.sort((a, b) => a[0] - b[0]);

  window.SCORE = {tempo: TEMPO, sections, outro, end: +(outro + OUTRO).toFixed(4), cuts, T, sfx, rests,
    intro: {lines: INTRO_LINES, typing, t0, rate}, stats: {t0: STAT_T0, gap: STAT_GAP, n: STATS}};
})();
