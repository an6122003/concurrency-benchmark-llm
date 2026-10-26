// The offline report's data layer: the same dash.data / dash.calc / dash.onData calls the
// dashboard version uses, reading the benchmark tables embedded in index.html (#rs-data).
(() => {
  const tables = JSON.parse(document.getElementById('rs-data').textContent);
  const calcs = [];
  const listeners = [];
  const data = { ...tables };
  let ready = false;

  const run = () => listeners.forEach((fn) => {
    try { fn(); } catch (e) { console.error(e); }
  });

  window.dash = {
    // Eight series colors for a light page, then the same names the dashboard tokens use.
    colors: ['#3a6fd8', '#e0662f', '#8b45c9', '#1f9e89', '#c23b7a', '#b8925a', '#5d6d7e', '#7fa32c'],
    data(id) {
      if (!(id in data)) return { status: ready ? 'missing' : 'loading', data: [], columns: [] };
      const rows = data[id];
      return { status: 'ok', data: rows, columns: rows.length ? Object.keys(rows[0]) : [] };
    },
    calc(id, spec) { calcs.push({ id, ...spec }); },
    onData(fn) {
      listeners.push(fn);
      if (ready) fn();
    },
    setLink(id) {
      try { history.replaceState(null, '', `#${id}`); } catch (e) { /* file:// pages may refuse */ }
    },
    params: () => ({}),
    setParams() {},
    resetParams() {},
    refresh() {},
  };

  window.addEventListener('DOMContentLoaded', () => {
    for (const c of calcs) {
      try {
        data[c.id] = c.fn(...c.inputs.map((id) => data[id] || []));
      } catch (e) {
        console.error(`calc ${c.id}`, e);
      }
    }
    ready = true;
    run();
  });
  let timer = null;
  let lastWidth = window.innerWidth;
  window.addEventListener('resize', () => {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    clearTimeout(timer);
    timer = setTimeout(run, 150);
  });
})();
