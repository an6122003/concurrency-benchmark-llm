// Charts, tables and screenshots for the RTX Spark report. index.html declares the calcs and window.RS.
const { ORDER, LINE_MODELS, color } = window.RS;
const MUTED = 'var(--cds-chart-muted)';
const NV = 'var(--rs-nv)';
const SPEC = ['none', 'mtp-n2', 'mtp-n3', 'dflash2'];
const KINDS = [['html_tps', 'HTML page'], ['python_tps', 'Python module'], ['prose_tps', 'Prose explanation']];
const RUN_ORDER = ['A', 'B-spill', 'A2'];
const RUN_LABEL = { A: 'Dedicated memory', 'B-spill': 'Shared memory', A2: 'Dedicated again' };
const DOCS = ['04_context_4k', '05_context_8k', '09_context_16k'];
const DOC_LABEL = { '04_context_4k': '4K words', '05_context_8k': '8K words', '09_context_16k': '16K words' };

const rowsOf = (id) => {
  const d = dash.data(id);
  return d.status === 'ok' && Array.isArray(d.data) ? d.data : [];
};
const rank = (key) => (ORDER.includes(key) ? ORDER.indexOf(key) : ORDER.length);
const shortOf = (models, key) => (models.find((m) => m.model === key) || {}).short || key;
const tinyOf = (models, key) => (models.find((m) => m.model === key) || {}).tiny || shortOf(models, key);
const kfmt = (d) => (Number(d) === 0 ? '0' : `${Number(d) / 1024}K`);
const depthHead = (d) => (Number(d) === 0 ? 'Empty context' : `${kfmt(d)} tokens in context`);
const people = (n) => `${n} ${Number(n) === 1 ? 'person' : 'people'} at once`;

// A value as its source holds it, with thousands separators: "2505" shows as "2,505", "14.0" stays "14.0".
function fmt(v) {
  if (v == null || v === '') return '—';
  const s = String(v);
  const m = /^(-?)(\d+)(\.\d+)?$/.exec(s);
  return m ? m[1] + Number(m[2]).toLocaleString('en-US') + (m[3] || '') : s;
}

// The row a mark names: its data-where pairs, its data-row, or the first row.
function pick(el) {
  const list = rowsOf(el.dataset.source);
  const where = el.getAttribute('data-where');
  if (where) {
    const pairs = where.split('&').map((p) => p.split('=').map((s) => decodeURIComponent(s)));
    return list.find((r) => pairs.every(([k, v]) => String(r[k]) === v));
  }
  return el.dataset.row != null ? list[Number(el.dataset.row)] : list[0];
}

function fillMarks() {
  for (const el of document.querySelectorAll('#dash-root [data-source][data-field]')) {
    if (el.tagName === 'TH') continue;
    const status = dash.data(el.dataset.source).status;
    el.classList.toggle('dash-skeleton', status === 'loading');
    const row = status === 'ok' ? pick(el) : null;
    el.textContent = row ? fmt(row[el.dataset.field]) : '—';
  }
}

function fillTables() {
  for (const table of document.querySelectorAll('#dash-root table[data-source][data-row-key]')) {
    const keys = table.dataset.rowKey.split(',');
    const heads = [...table.tHead.rows[0].cells];
    const list = rowsOf(table.dataset.source).slice();
    if (keys[0] === 'model') list.sort((a, b) => rank(a.model) - rank(b.model));
    table.tBodies[0].replaceChildren(...list.map((r) => {
      const tr = document.createElement('tr');
      tr.dataset.key = keys.length > 1 ? keys.map((k) => encodeURIComponent(String(r[k]))).join(',') : String(r[keys[0]]);
      for (const th of heads) {
        const td = document.createElement('td');
        if (th.classList.contains('txt')) td.className = 'txt';
        // A raw column (a year, a date) shows its value as written, without thousands separators.
        td.textContent = th.classList.contains('raw') ? (r[th.dataset.field] || '—') : fmt(r[th.dataset.field]);
        tr.append(td);
      }
      return tr;
    }));
  }
}

// Empties a chart box and says whether all its sources are ready; a failed source shows one line.
function frame(box) {
  const states = box.dataset.source.split(' ').map((id) => dash.data(id).status);
  box.replaceChildren();
  box.classList.toggle('dash-skeleton', states.includes('loading'));
  if (states.every((s) => s === 'ok')) return box.clientWidth > 40;
  if (!states.includes('loading')) {
    const line = document.createElement('div');
    line.className = 'rs-fail';
    const dot = document.createElement('span');
    dot.className = 'dot';
    line.append(dot, 'Failed to load');
    box.append(line);
  }
  return false;
}

const drawn = new Set();
// Holds the box at its drawn height, and fades a chart in the first time it has data.
function done(box, svg) {
  const top = box.getBoundingClientRect().top;
  box.style.minHeight = `${Math.ceil(svg.node().getBoundingClientRect().bottom - top)}px`;
  if (!drawn.has(box.id)) {
    drawn.add(box.id);
    svg.classed('rs-in', true);
  }
}

function textWidths(svg, texts, cls) {
  const g = svg.append('g').style('visibility', 'hidden');
  const widths = texts.map((t) => g.append('text').attr('class', cls || null).text(t).node().getComputedTextLength());
  g.remove();
  return widths;
}

function tipFor(box) {
  const el = document.createElement('div');
  el.className = 'rs-tip';
  box.append(el);
  return {
    show(event, head, lines) {
      const [x, y] = d3.pointer(event, box);
      el.replaceChildren();
      if (head) {
        const h = document.createElement('div');
        h.className = 'h';
        h.textContent = head;
        el.append(h);
      }
      for (const line of lines) {
        const row = document.createElement('div');
        if (line.color) {
          const sw = document.createElement('span');
          sw.className = 'sw';
          sw.style.background = line.color;
          row.append(sw);
        }
        row.append(line.text);
        el.append(row);
      }
      el.style.display = 'block';
      const w = el.offsetWidth, h = el.offsetHeight;
      el.style.left = `${Math.max(0, x + 14 + w > box.clientWidth ? x - 14 - w : x + 14)}px`;
      el.style.top = `${y - h - 10 < 0 ? y + 14 : y - h - 10}px`;
    },
    hide() {
      el.style.display = 'none';
    },
  };
}

// Horizontal bars, one row per item (an item with `head` is a group title). Labels sit left of
// the bars, or above them when the box is too narrow for that.
function hbar(box, items) {
  const W = box.clientWidth;
  const svg = d3.select(box).append('svg').attr('width', '100%');
  const bars = items.filter((d) => !d.head);
  const labelW = d3.max(textWidths(svg, bars.map((d) => d.label), 'lbl')) || 0;
  const valueW = d3.max(textWidths(svg, bars.map((d) => d.text), 'val')) || 0;
  const stacked = labelW + 12 > W * 0.42;
  const left = stacked ? 0 : labelW + 12;
  const barH = stacked ? 12 : 18;
  const rowH = stacked ? 34 : 28;
  const x = d3.scaleLinear([0, d3.max(bars, (d) => d.value) || 1], [left, Math.max(left + 24, W - valueW - 8)]);
  const tip = tipFor(box);
  let y = 0;
  for (const d of items) {
    if (d.head) {
      svg.append('text').attr('class', 'lbl head').attr('x', 0).attr('y', y + 16).text(d.head);
      y += 24;
      continue;
    }
    const g = svg.append('g').attr('transform', `translate(0,${y})`);
    const by = stacked ? 17 : (rowH - barH) / 2;
    if (stacked) g.append('text').attr('class', 'lbl').attr('x', 0).attr('y', 12).text(d.label);
    else g.append('text').attr('class', 'lbl').attr('x', left - 10).attr('y', by + barH / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text(d.label);
    g.append('rect').attr('x', left).attr('y', by).attr('height', barH).attr('rx', 4)
      .attr('width', Math.max(2, x(d.value) - left)).style('fill', d.color).style('fill-opacity', d.opacity ?? 1);
    g.append('text').attr('class', 'val').attr('x', x(d.value) + 6).attr('y', by + barH / 2).attr('dy', '0.35em').text(d.text);
    g.append('rect').attr('width', W).attr('height', rowH).style('fill', 'transparent')
      .on('pointermove', (e) => tip.show(e, d.tipHead || d.label, d.tip || [{ text: d.text }]))
      .on('pointerleave', () => tip.hide());
    y += rowH;
  }
  svg.attr('viewBox', `0 0 ${W} ${y}`).attr('height', y);
  return svg;
}

// Lines over a shared x. Each line ends in its name and last value (a legend above it when the
// box is narrow); hovering marks the nearest x and lists every series there.
function lineChart(box, series, o) {
  const W = box.clientWidth, H = o.height || 240;
  const svg = d3.select(box).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('height', H);
  const xs = o.xs || [...new Set(series.flatMap((s) => s.points.map((p) => p.x)))].sort((a, b) => a - b);
  const top = 10, bottom = H - 24;
  const yMax = Math.max(o.yMax || 0, (d3.max(series, (s) => d3.max(s.points, (p) => p.y)) || 1) * 1.06);
  const y = d3.scaleLinear([0, yMax], [bottom, top]).nice(4);
  const ticks = y.ticks(4);
  const tickW = d3.max(textWidths(svg, ticks.map(o.yFmt))) || 0;
  const ends = series.filter((s) => s.points.length).map((s) => {
    const p = s.points[s.points.length - 1];
    return { s, p, text: `${s.label} ${o.endFmt(p)}` };
  });
  const endW = d3.max(textWidths(svg, ends.map((e) => e.text), 'lbl')) || 0;
  const legend = endW + 26 > W * 0.42;
  const left = tickW + 10;
  const right = legend ? W - 8 : W - endW - 26;
  const range = [left + 8, right];
  const x = o.log ? d3.scaleLog(d3.extent(xs), range).base(2) : o.linear ? d3.scaleLinear(d3.extent(xs), range) : d3.scalePoint(xs, range);

  for (const t of ticks) {
    svg.append('line').attr('class', 'grid').attr('x1', left).attr('x2', right).attr('y1', y(t)).attr('y2', y(t));
    svg.append('text').attr('x', left - 8).attr('y', y(t)).attr('dy', '0.35em').attr('text-anchor', 'end').text(o.yFmt(t));
  }
  svg.append('line').attr('class', 'axis').attr('x1', left).attr('x2', right).attr('y1', y(0)).attr('y2', y(0));
  // x labels left to right, dropping any that would touch the one before or the last one, which always shows.
  const labels = xs.map((v) => {
    const text = o.xFmt(v);
    const w = textWidths(svg, [text])[0];
    return { text, w, cx: Math.min(Math.max(x(v), left + w / 2), W - w / 2) };
  });
  const last = labels[labels.length - 1];
  let lastRight = -Infinity;
  for (const l of labels) {
    if (l !== last && (l.cx - l.w / 2 < lastRight + 8 || l.cx + l.w / 2 > last.cx - last.w / 2 - 8)) continue;
    svg.append('text').attr('x', l.cx).attr('y', H - 6).attr('text-anchor', 'middle').text(l.text);
    lastRight = l.cx + l.w / 2;
  }
  if (o.ref) {
    svg.append('line').attr('class', 'rule').attr('x1', left).attr('x2', right).attr('y1', y(o.ref.value)).attr('y2', y(o.ref.value))
      .style('stroke-dasharray', '4 4');
    svg.append('text').attr('class', 'ref').attr('x', right).attr('y', y(o.ref.value) - 5).attr('text-anchor', 'end').text(o.ref.label);
  }

  const line = d3.line().x((p) => x(p.x)).y((p) => y(p.y));
  for (const s of series) {
    svg.append('path').attr('class', 'line').attr('d', line(s.points)).style('stroke', s.color).style('stroke-dasharray', s.dash ? '5 4' : null);
    svg.selectAll(null).data(s.points).join('circle').attr('cx', (p) => x(p.x)).attr('cy', (p) => y(p.y)).attr('r', 2.5).style('fill', s.color);
  }

  if (legend) {
    const lg = document.createElement('div');
    lg.className = 'rs-legend';
    for (const s of series) {
      const item = document.createElement('span');
      const sw = document.createElement('i');
      sw.style.background = s.color;
      item.append(sw, s.label);
      lg.append(item);
    }
    box.insertBefore(lg, svg.node());
  } else {
    // End labels in value order, pushed apart so none touch, then pulled back inside the plot.
    const placed = ends.map((e) => ({ ...e, ly: y(e.p.y) })).sort((a, b) => a.ly - b.ly);
    for (let i = 1; i < placed.length; i++) placed[i].ly = Math.max(placed[i].ly, placed[i - 1].ly + 14);
    if (placed.length && placed[placed.length - 1].ly > bottom) {
      placed[placed.length - 1].ly = bottom;
      for (let i = placed.length - 2; i >= 0; i--) placed[i].ly = Math.min(placed[i].ly, placed[i + 1].ly - 14);
    }
    for (const e of placed) {
      svg.append('line').attr('x1', x(e.p.x) + 4).attr('x2', right + 18).attr('y1', y(e.p.y)).attr('y2', e.ly)
        .style('stroke', e.s.color).style('stroke-opacity', 0.6);
      svg.append('text').attr('class', 'lbl').attr('x', right + 22).attr('y', e.ly).attr('dy', '0.35em').text(e.text);
    }
  }

  const hover = svg.append('g').style('display', 'none');
  const rule = hover.append('line').attr('class', 'rule').attr('y1', top).attr('y2', bottom);
  const dots = hover.selectAll(null).data(series).join('circle').attr('r', 4)
    .style('fill', (s) => s.color).style('stroke', 'var(--color-panel)').style('stroke-width', 2);
  const tip = tipFor(box);
  svg.append('rect').attr('x', left).attr('y', top).attr('width', Math.max(0, right - left + 8)).attr('height', bottom - top)
    .style('fill', 'transparent')
    .on('pointermove', (e) => {
      const [mx] = d3.pointer(e, svg.node());
      const xv = xs.reduce((a, v) => (Math.abs(x(v) - mx) < Math.abs(x(a) - mx) ? v : a), xs[0]);
      rule.attr('x1', x(xv)).attr('x2', x(xv));
      dots.each(function (s) {
        const p = s.points.find((q) => q.x === xv);
        d3.select(this).style('display', p ? null : 'none').attr('cx', x(xv)).attr('cy', p ? y(p.y) : 0);
      });
      hover.style('display', null);
      const at = series.map((s) => ({ s, p: s.points.find((q) => q.x === xv) })).filter((d) => d.p).sort((a, b) => b.p.y - a.p.y);
      tip.show(e, o.tipHead(xv), at.map((d) => ({ color: d.s.color, text: `${d.s.label}: ${o.tipFmt(d.p)}` })));
    })
    .on('pointerleave', () => {
      hover.style('display', 'none');
      tip.hide();
    });
  return svg;
}

function speedBars(id, test) {
  const box = document.getElementById(id);
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const items = rowsOf('bench').filter((r) => r.set === 'classic' && r.test === test && ORDER.includes(r.model))
    .sort((a, b) => Number(b.tps) - Number(a.tps))
    .map((r) => ({ label: tinyOf(models, r.model), value: Number(r.tps), text: `${fmt(r.tps)} tok/s`, color: color(r.model),
      tipHead: shortOf(models, r.model), tip: [{ text: `${fmt(r.tps)} ± ${fmt(r.sd)} tok/s` }] }));
  done(box, hbar(box, items));
}

function depthChart(id, test) {
  const box = document.getElementById(id);
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const keep = rowsOf('depthkeep').filter((r) => r.test === test);
  const series = LINE_MODELS.map((m) => ({ label: tinyOf(models, m), color: color(m),
    points: keep.filter((r) => r.model === m).sort((a, b) => a.depth - b.depth).map((r) => ({ x: r.depth, y: r.pct, tps: r.tps })) }))
    .filter((s) => s.points.length);
  done(box, lineChart(box, series, {
    yMax: 100, xFmt: kfmt, yFmt: (v) => `${v}%`, endFmt: (p) => `${p.y}%`,
    tipHead: depthHead, tipFmt: (p) => `${fmt(p.tps)} tok/s (${p.y}%)`,
  }));
}

function dgxChart(id, test) {
  const box = document.getElementById(id);
  if (!box || !frame(box)) return;
  const rows = rowsOf('dgx').filter((r) => r.test === test);
  const series = [['RTX Spark laptop', NV], ['DGX Spark', MUTED]].map(([machine, c]) => ({ label: machine, color: c,
    points: rows.filter((r) => r.machine === machine).map((r) => ({ x: Number(r.depth), y: Number(r.tps), raw: r.tps })).sort((a, b) => a.x - b.x) }));
  done(box, lineChart(box, series, {
    xFmt: kfmt, yFmt: d3.format(','), endFmt: (p) => fmt(p.raw), tipHead: depthHead, tipFmt: (p) => `${fmt(p.raw)} tok/s`,
  }));
}

// Speculative configurations share Qwen3.8-27B's color, stronger as the draft gets better.
const specShade = (config) => (config === 'none' ? { color: MUTED }
  : { color: color('qwen3.8-27b'), opacity: { 'mtp-n2': 0.45, 'mtp-n3': 0.7 }[config] ?? 1 });

function specChart() {
  const box = document.getElementById('spec-chart');
  if (!box || !frame(box)) return;
  const spec = rowsOf('spec').slice().sort((a, b) => SPEC.indexOf(a.config) - SPEC.indexOf(b.config));
  done(box, hbar(box, spec.map((r) => ({ label: r.config_label, value: Number(r.gen_tps), ...specShade(r.config),
    text: r.acceptance_pct ? `${fmt(r.gen_tps)} tok/s · ${fmt(r.acceptance_pct)}% accepted` : `${fmt(r.gen_tps)} tok/s` }))));
}

function specKindChart() {
  const box = document.getElementById('spec-kind-chart');
  if (!box || !frame(box)) return;
  const spec = rowsOf('spec').slice().sort((a, b) => SPEC.indexOf(a.config) - SPEC.indexOf(b.config));
  const items = KINDS.flatMap(([field, name]) => [{ head: name }, ...spec.map((r) => ({ label: r.config_label, value: Number(r[field]),
    text: `${fmt(r[field])} tok/s`, tipHead: `${name}, ${r.config_label}`, ...specShade(r.config) }))]);
  done(box, hbar(box, items));
}

function sharedChart() {
  const box = document.getElementById('shared-chart');
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const shared = rowsOf('shared');
  const items = [...new Set(shared.map((r) => r.model))].sort((a, b) => rank(a) - rank(b)).flatMap((m) => [{ head: tinyOf(models, m) },
    ...RUN_ORDER.map((run) => shared.find((r) => r.model === m && r.run === run)).filter(Boolean).map((r) => ({
      label: RUN_LABEL[r.run], value: Number(r.tg128), text: `${fmt(r.tg128)} tok/s`, color: color(m),
      opacity: r.placement === 'shared' ? 0.45 : 1, tipHead: `${tinyOf(models, m)}, ${RUN_LABEL[r.run].toLowerCase()}`,
      tip: [{ text: `writing ${fmt(r.tg128)} tok/s, reading ${fmt(r.pp512)} tok/s` },
        { text: `${fmt(r.dedicated_gb)} GB dedicated, ${fmt(r.shared_gb)} GB shared` }] }))]);
  done(box, hbar(box, items));
}

function powerChart() {
  const box = document.getElementById('power-chart');
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const items = rowsOf('power').filter((r) => r.phase === 'bench' && ORDER.includes(r.model))
    .sort((a, b) => Number(b.power_busy_avg_w) - Number(a.power_busy_avg_w))
    .map((r) => ({ label: tinyOf(models, r.model), value: Number(r.power_busy_avg_w), text: `${fmt(r.power_busy_avg_w)} W`, color: color(r.model),
      tipHead: shortOf(models, r.model), tip: [{ text: `average ${fmt(r.power_busy_avg_w)} W, peak ${fmt(r.power_max_w)} W` },
        { text: `up to ${fmt(r.temp_max_c)} °C, ${fmt(r.clock_busy_avg_mhz)} MHz average clock` }] }));
  done(box, hbar(box, items));
}

function teamChart(id, field, o) {
  const box = document.getElementById(id);
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const team = rowsOf('conc').filter((r) => r.mode === 'baseline' && (r.scenario === '02_team_concurrency' || r.scenario === '10_team_stress'));
  const series = ORDER.filter((m) => team.some((r) => r.model === m)).map((m) => ({ label: tinyOf(models, m), color: color(m),
    points: team.filter((r) => r.model === m).map((r) => ({ x: Number(r.users), y: Number(r[field]), raw: r[field] })).sort((a, b) => a.x - b.x) }));
  done(box, lineChart(box, series, { log: true, xFmt: String, endFmt: (p) => fmt(p.raw), tipHead: people, ...o }));
}

function batchedChart() {
  const box = document.getElementById('batched-chart');
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const rows = rowsOf('batched');
  const series = ORDER.filter((m) => rows.some((r) => r.model === m)).map((m) => ({ label: tinyOf(models, m), color: color(m),
    points: rows.filter((r) => r.model === m)
      .map((r) => ({ x: Number(r.parallel), y: Number(r.decode_tps), raw: r.decode_tps, each: r.per_stream_tps })).sort((a, b) => a.x - b.x) }));
  done(box, lineChart(box, series, {
    log: true, xFmt: String, yFmt: d3.format(','), endFmt: (p) => fmt(p.raw),
    tipHead: (n) => `${n} parallel ${Number(n) === 1 ? 'sequence' : 'sequences'}`, tipFmt: (p) => `${fmt(p.raw)} tok/s in total, ${fmt(p.each)} each`,
  }));
}

function mtpChart() {
  const box = document.getElementById('mtp-chart');
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const rows = rowsOf('conc').filter((r) => r.scenario === '02_team_concurrency');
  const levels = new Set(rows.filter((r) => r.mode === 'mtp').map((r) => Number(r.users)));
  const series = ORDER.filter((m) => rows.some((r) => r.model === m && r.mode === 'mtp')).flatMap((m) => ['baseline', 'mtp'].map((mode) => ({
    label: `${tinyOf(models, m)}${mode === 'mtp' ? ' + MTP' : ''}`, color: color(m), dash: mode === 'mtp',
    points: rows.filter((r) => r.model === m && r.mode === mode && levels.has(Number(r.users)))
      .map((r) => ({ x: Number(r.users), y: Number(r.per_user_tps), raw: r.per_user_tps })).sort((a, b) => a.x - b.x) })));
  done(box, lineChart(box, series, {
    log: true, xFmt: String, yFmt: String, endFmt: (p) => fmt(p.raw), tipHead: people, tipFmt: (p) => `${fmt(p.raw)} tok/s each`,
  }));
}

function docChart(id, field, unit, yFmt) {
  const box = document.getElementById(id);
  if (!box || !frame(box)) return;
  const models = rowsOf('models');
  const rows = rowsOf('docsum');
  const series = ORDER.filter((m) => rows.some((r) => r.model === m)).map((m) => ({ label: tinyOf(models, m), color: color(m),
    points: DOCS.map((s) => rows.find((r) => r.model === m && r.scenario === s)).filter(Boolean)
      .map((r) => ({ x: r.scenario, y: Number(r[field]), raw: r[field], tokens: r.prompt_tokens })) }));
  done(box, lineChart(box, series, {
    xs: DOCS, xFmt: (s) => DOC_LABEL[s], yFmt, endFmt: (p) => fmt(p.raw),
    tipHead: (s) => `${DOC_LABEL[s]} document`, tipFmt: (p) => `${fmt(p.raw)} ${unit} (${fmt(p.tokens)} prompt tokens)`,
  }));
}

// Screenshots of the generated apps come from shots.js as data URLs.
function drawShots() {
  const box = document.getElementById('shots');
  const shots = window.RS_SHOTS || [];
  if (!box || box.childElementCount || !shots.length) return;
  for (const s of shots) {
    const fig = document.createElement('figure');
    const img = document.createElement('img');
    img.src = s.src;
    img.alt = s.alt;
    img.loading = 'lazy';
    const cap = document.createElement('figcaption');
    cap.textContent = s.caption;
    fig.append(img, cap);
    box.append(fig);
  }
}

const go = (el) => {
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  dash.setLink(el.id);
};
for (const a of document.querySelectorAll('#dash-root [data-go]')) {
  a.addEventListener('click', (e) => {
    const el = document.getElementById(a.dataset.go);
    if (!el) return;
    e.preventDefault();
    go(el);
  });
}
const watch = new IntersectionObserver((entries) => {
  for (const e of entries) if (e.isIntersecting) dash.setLink(e.target.id);
}, { root: document, rootMargin: '-15% 0px -75% 0px' });
document.querySelectorAll('#dash-root .rs-sec[id]').forEach((s) => watch.observe(s));

let linked = false;
dash.onData(() => {
  fillMarks();
  fillTables();
  speedBars('decode-chart', 'tg128');
  speedBars('prefill-chart', 'pp512');
  depthChart('depth-tg-chart', 'tg32');
  depthChart('depth-pp-chart', 'pp2048');
  teamChart('team-user-chart', 'per_user_tps', { yFmt: String, tipFmt: (p) => `${fmt(p.raw)} tok/s each`, ref: { value: 10, label: '10 tok/s each' } });
  teamChart('team-agg-chart', 'agg_tps', { yFmt: d3.format(','), tipFmt: (p) => `${fmt(p.raw)} tok/s in total` });
  teamChart('team-ttft-chart', 'avg_ttft_s', { yFmt: String, tipFmt: (p) => `${fmt(p.raw)} s to the first word`, ref: { value: 2, label: '2 s' } });
  batchedChart();
  docChart('doc-ttft-chart', 'ttft_s', 's', String);
  docChart('doc-pp-chart', 'prefill_tps', 'tok/s', d3.format(','));
  specChart();
  specKindChart();
  mtpChart();
  sharedChart();
  dgxChart('dgx-tg-chart', 'tg32');
  dgxChart('dgx-pp-chart', 'pp2048');
  powerChart();
  drawShots();
  if (!linked && !document.querySelector('#dash-root .rs-chart.dash-skeleton')) {
    linked = true;
    const named = location.hash && document.getElementById(location.hash.slice(1));
    if (named) requestAnimationFrame(() => go(named));
  }
});
