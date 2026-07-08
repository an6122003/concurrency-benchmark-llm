// Landing page: live stats + leaderboard from the API, falling back to
// sample-data.json when opened without the backend.

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

/* ---------- scroll reveal ---------- */

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach(el => observer.observe(el));

/* ---------- animated count-up ---------- */

function countUp(el, target, format) {
  const duration = 1100;
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = format(target * eased);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function setStat(name, value, format) {
  const el = document.querySelector(`[data-stat="${name}"]`);
  if (!el) return;
  if (value === null || value === undefined) { el.textContent = "–"; return; }
  const statObserver = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      countUp(el, value, format);
      statObserver.disconnect();
    }
  }, { threshold: 0.4 });
  statObserver.observe(el);
}

/* ---------- data loading ---------- */

function summarizeRuns(runs) {
  const nums = key => runs.map(r => r.benchmark[key]).filter(v => v !== null && v !== undefined);
  return {
    runs: runs.length,
    best_users: Math.max(0, ...nums("comfortableUsers")) || null,
    top_tps: Math.max(0, ...nums("peakAggregateTps")) || null,
    best_value: nums("pricePerComfortableUser").sort((a, b) => a - b)[0] ?? null
  };
}

function topRuns(runs, n) {
  return [...runs]
    .sort((a, b) => (b.benchmark.comfortableUsers || 0) - (a.benchmark.comfortableUsers || 0) ||
                    (b.benchmark.peakAggregateTps || 0) - (a.benchmark.peakAggregateTps || 0))
    .slice(0, n);
}

function renderPodium(runs) {
  const podium = document.getElementById("podium");
  if (!runs.length) {
    podium.innerHTML = '<div class="podium-empty">No runs yet — be the first to import a benchmark.</div>';
    return;
  }
  podium.innerHTML = runs.map((run, index) => {
    const bench = run.benchmark;
    const ttft = bench.ttft1u ?? bench.runPoints?.[0]?.ttft;
    return `
      <a class="podium-card rank-${index + 1}" href="run.html?id=${encodeURIComponent(run.id)}">
        <div class="rank-badge">#${index + 1}</div>
        <h3>${escapeHtml(run.hardware.model)}</h3>
        <div class="podium-sub">${escapeHtml(run.model.name)} · ${escapeHtml(run.software.runtime)} · ${escapeHtml(run.software.backend || "")}</div>
        <div class="podium-metrics">
          <div><span>Comfortable users</span><strong>${bench.comfortableUsers ?? "–"}</strong></div>
          <div><span>Peak tok/s</span><strong>${bench.peakAggregateTps ? bench.peakAggregateTps.toFixed(1) : "–"}</strong></div>
          <div><span>TTFT</span><strong>${ttft ? ttft.toFixed(2) + "s" : "–"}</strong></div>
          <div><span>VRAM</span><strong>${run.hardware.vramGb ? run.hardware.vramGb + " GB" : "–"}</strong></div>
        </div>
      </a>
    `;
  }).join("");
}

function applyStats(stats) {
  setStat("runs", stats.runs, v => Math.round(v).toLocaleString());
  setStat("best_users", stats.best_users, v => Math.round(v).toString());
  setStat("top_tps", stats.top_tps, v => v.toFixed(1));
  setStat("best_value", stats.best_value, v => `$${Math.round(v)}`);
}

async function boot() {
  try {
    const [statsRes, runsRes] = await Promise.all([
      fetch("/api/stats"),
      fetch("/api/runs?sort=comfortable_users&limit=3")
    ]);
    if (statsRes.ok && runsRes.ok) {
      applyStats(await statsRes.json());
      renderPodium((await runsRes.json()).runs);
      return;
    }
  } catch (err) {
    // no backend — static fallback below
  }
  try {
    const runs = await (await fetch("sample-data.json")).json();
    applyStats(summarizeRuns(runs));
    renderPodium(topRuns(runs, 3));
  } catch (err) {
    document.getElementById("podium").innerHTML =
      `<div class="podium-empty">Could not load data: ${escapeHtml(err.message)}</div>`;
  }
}

boot();
lucide.createIcons();
