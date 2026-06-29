let allRuns = [];
let visibleRuns = [];
let selectedId = null;
let activePreset = "";
let throughputChart;
let brandChart;

const els = {
  search: document.getElementById("searchInput"),
  brand: document.getElementById("brandFilter"),
  family: document.getElementById("familyFilter"),
  runtime: document.getElementById("runtimeFilter"),
  backend: document.getElementById("backendFilter"),
  quant: document.getElementById("quantFilter"),
  os: document.getElementById("osFilter"),
  vram: document.getElementById("vramFilter"),
  users: document.getElementById("usersFilter"),
  vramValue: document.getElementById("vramValue"),
  usersValue: document.getElementById("usersValue"),
  sort: document.getElementById("sortSelect"),
  body: document.getElementById("resultsBody"),
  activeFilters: document.getElementById("activeFilters"),
  detail: document.getElementById("detailPanel"),
  visibleRuns: document.getElementById("visibleRuns"),
  bestUsers: document.getElementById("bestUsers"),
  topThroughput: document.getElementById("topThroughput"),
  bestValue: document.getElementById("bestValue"),
  importBtn: document.getElementById("importBtn"),
  importFile: document.getElementById("importFile"),
  resetBtn: document.getElementById("resetBtn")
};

const optionFields = [
  ["brand", "hardware.brand"],
  ["family", "model.family"],
  ["runtime", "software.runtime"],
  ["backend", "software.backend"],
  ["quant", "model.quantization"],
  ["os", "system.os"]
];

function get(obj, path) {
  return path.split(".").reduce((acc, key) => acc && acc[key], obj);
}

function uniqueValues(path) {
  return [...new Set(allRuns.map(item => get(item, path)).filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b)));
}

function fillSelect(select, values, label) {
  select.innerHTML = [`<option value="">All ${label}</option>`, ...values.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)].join("");
}

function setupFilters() {
  optionFields.forEach(([id, path]) => fillSelect(els[id], uniqueValues(path), id));
}

function readFilters() {
  return {
    search: els.search.value.trim().toLowerCase(),
    brand: els.brand.value,
    family: els.family.value,
    runtime: els.runtime.value,
    backend: els.backend.value,
    quant: els.quant.value,
    os: els.os.value,
    minVram: Number(els.vram.value),
    users: Number(els.users.value)
  };
}

function matchSearch(run, search) {
  if (!search) return true;
  const haystack = [
    run.hardware.brand,
    run.hardware.model,
    run.hardware.boardPartner,
    run.model.family,
    run.model.name,
    run.model.quantization,
    run.software.runtime,
    run.software.backend,
    run.software.driver,
    run.system.os,
    run.system.cpu
  ].join(" ").toLowerCase();
  return haystack.includes(search);
}

function runMatches(run, filters) {
  const presetMatch =
    !activePreset ||
    (activePreset === "team" && run.benchmark.comfortableUsers >= 5) ||
    (activePreset === "thirtyB" && run.model.sizeB >= 30) ||
    (activePreset === "budget" && run.hardware.priceUsd <= 1000) ||
    (activePreset === "nonCuda" && !run.software.backend.toLowerCase().includes("cuda")) ||
    (activePreset === "lowLatency" && (run.benchmark.runPoints[0]?.ttft || 99) <= 0.75);
  return presetMatch &&
    matchSearch(run, filters.search) &&
    (!filters.brand || run.hardware.brand === filters.brand) &&
    (!filters.family || run.model.family === filters.family) &&
    (!filters.runtime || run.software.runtime === filters.runtime) &&
    (!filters.backend || run.software.backend === filters.backend) &&
    (!filters.quant || run.model.quantization === filters.quant) &&
    (!filters.os || run.system.os === filters.os) &&
    run.hardware.vramGb >= filters.minVram &&
    run.benchmark.comfortableUsers >= filters.users;
}

function sortRuns(runs) {
  const key = els.sort.value;
  const sorted = [...runs];
  sorted.sort((a, b) => {
    if (key === "vramGb") return b.hardware.vramGb - a.hardware.vramGb;
    if (key === "pricePerComfortableUser") return a.benchmark.pricePerComfortableUser - b.benchmark.pricePerComfortableUser;
    return b.benchmark[key] - a.benchmark[key];
  });
  return sorted;
}

function applyFilters() {
  const filters = readFilters();
  els.vramValue.textContent = `${filters.minVram} GB`;
  els.usersValue.textContent = `${filters.users}+`;
  visibleRuns = sortRuns(allRuns.filter(run => runMatches(run, filters)));
  if (!visibleRuns.some(run => run.id === selectedId)) selectedId = visibleRuns[0]?.id || null;
  render();
}

function fmt(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(digits);
}

function money(value) {
  if (value === null || value === undefined) return "-";
  return `$${Math.round(value).toLocaleString()}`;
}

function renderMetrics() {
  const bestUsers = Math.max(0, ...visibleRuns.map(run => run.benchmark.comfortableUsers));
  const topTps = Math.max(0, ...visibleRuns.map(run => run.benchmark.peakAggregateTps));
  const valueRun = visibleRuns.filter(run => run.benchmark.pricePerComfortableUser).sort((a, b) => a.benchmark.pricePerComfortableUser - b.benchmark.pricePerComfortableUser)[0];
  els.visibleRuns.textContent = visibleRuns.length;
  els.bestUsers.textContent = bestUsers ? `${bestUsers} users` : "-";
  els.topThroughput.textContent = topTps ? `${fmt(topTps)} tok/s` : "-";
  els.bestValue.textContent = valueRun ? money(valueRun.benchmark.pricePerComfortableUser) : "-";
}

function renderChips() {
  const filters = readFilters();
  const chips = [];
  for (const [key, value] of Object.entries(filters)) {
    if (!value || value === 0 || (key === "users" && value === 1)) continue;
    chips.push(`<span class="chip">${escapeHtml(key)}: ${escapeHtml(value)}</span>`);
  }
  if (activePreset) chips.push(`<span class="chip">preset: ${escapeHtml(activePreset)}</span>`);
  els.activeFilters.innerHTML = chips.join("");
}

function renderTable() {
  els.body.innerHTML = visibleRuns.map(run => {
    const firstPoint = run.benchmark.runPoints[0] || {};
    const cls = run.benchmark.verified.toLowerCase();
    return `
      <tr data-id="${escapeHtml(run.id)}" class="${run.id === selectedId ? "selected" : ""}">
        <td><div class="main-cell"><strong>${escapeHtml(run.hardware.model)}</strong><span>${escapeHtml(run.hardware.brand)} · ${escapeHtml(run.hardware.class)} · <span class="${cls}">${escapeHtml(run.benchmark.verified)}</span></span></div></td>
        <td><div class="main-cell"><strong>${escapeHtml(run.model.name)}</strong><span>${run.model.sizeB}B · ${escapeHtml(run.model.quantization)} · ${run.model.context.toLocaleString()} ctx</span></div></td>
        <td><div class="main-cell"><strong>${escapeHtml(run.software.runtime)}</strong><span>${escapeHtml(run.software.backend)}</span></div></td>
        <td>${run.hardware.vramGb} GB</td>
        <td>${run.benchmark.comfortableUsers}</td>
        <td>${fmt(run.benchmark.peakAggregateTps)}</td>
        <td>${fmt(firstPoint.ttft, 2)}s</td>
        <td>${fmt(firstPoint.p95Latency, 1)}s</td>
        <td>${money(run.benchmark.pricePerComfortableUser)}</td>
      </tr>
    `;
  }).join("");
}

function renderDetail() {
  const run = visibleRuns.find(item => item.id === selectedId);
  if (!run) {
    els.detail.innerHTML = '<div class="empty-detail">Select a run to inspect concurrency points, software, and hardware metadata.</div>';
    return;
  }
  const rows = run.benchmark.runPoints.map(point => `
    <tr>
      <td>${point.users}</td>
      <td>${fmt(point.aggregateTps)}</td>
      <td>${fmt(point.perUserTps)}</td>
      <td>${fmt(point.ttft, 2)}s</td>
      <td>${fmt(point.p95Latency, 1)}s</td>
      <td>${fmt(point.successRate, 0)}%</td>
      <td>${fmt(point.vramUsedGb)} GB</td>
    </tr>
  `).join("");
  els.detail.innerHTML = `
    <div class="panel-head">
      <h2>${escapeHtml(run.hardware.model)} · ${escapeHtml(run.model.name)}</h2>
      <span class="chip">${escapeHtml(run.benchmark.verified)}</span>
    </div>
    <div class="detail-grid">
      <div class="detail-card">
        <h3>Hardware</h3>
        <div class="kv">
          <span>Brand</span><span>${escapeHtml(run.hardware.brand)}</span>
          <span>VRAM</span><span>${run.hardware.vramGb} GB ${escapeHtml(run.hardware.memoryType)}</span>
          <span>Bus</span><span>${run.hardware.busWidth || "-"} bit</span>
          <span>Price</span><span>${money(run.hardware.priceUsd)}</span>
        </div>
      </div>
      <div class="detail-card">
        <h3>Stack</h3>
        <div class="kv">
          <span>Runtime</span><span>${escapeHtml(run.software.runtime)}</span>
          <span>Backend</span><span>${escapeHtml(run.software.backend)}</span>
          <span>Endpoint</span><span>${escapeHtml(run.software.endpoint)}</span>
          <span>OS</span><span>${escapeHtml(run.system.os)}</span>
        </div>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Users</th><th>Aggregate tok/s</th><th>Per-user tok/s</th><th>TTFT</th><th>P95 latency</th><th>Success</th><th>VRAM used</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderCharts() {
  const labels = visibleRuns.map(run => `${run.hardware.model} · ${run.model.sizeB}B`);
  const throughput = visibleRuns.map(run => run.benchmark.peakAggregateTps);
  const users = visibleRuns.map(run => run.benchmark.comfortableUsers);
  if (throughputChart) throughputChart.destroy();
  throughputChart = new Chart(document.getElementById("throughputChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Peak aggregate tok/s", data: throughput, backgroundColor: "#8070f8", yAxisID: "y" },
        { label: "Comfortable users", data: users, backgroundColor: "#60d8c0", yAxisID: "y1" }
      ]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "rgba(255,255,255,.75)" } } },
      scales: {
        x: { ticks: { color: "rgba(255,255,255,.55)", maxRotation: 45, minRotation: 0 }, grid: { color: "rgba(255,255,255,.06)" } },
        y: { beginAtZero: true, ticks: { color: "rgba(255,255,255,.55)" }, grid: { color: "rgba(255,255,255,.06)" } },
        y1: { beginAtZero: true, position: "right", ticks: { color: "rgba(255,255,255,.55)", precision: 0 }, grid: { drawOnChartArea: false } }
      }
    }
  });

  const counts = visibleRuns.reduce((acc, run) => {
    acc[run.hardware.brand] = (acc[run.hardware.brand] || 0) + 1;
    return acc;
  }, {});
  if (brandChart) brandChart.destroy();
  brandChart = new Chart(document.getElementById("brandChart"), {
    type: "doughnut",
    data: {
      labels: Object.keys(counts),
      datasets: [{ data: Object.values(counts), backgroundColor: ["#8070f8", "#58c8f8", "#60d8c0", "#a090f8", "#ffffff"] }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { color: "rgba(255,255,255,.75)" } } }
    }
  });
}

function render() {
  renderMetrics();
  renderChips();
  renderTable();
  renderDetail();
  renderCharts();
  lucide.createIcons();
}

function resetFilters() {
  activePreset = "";
  els.search.value = "";
  optionFields.forEach(([id]) => { els[id].value = ""; });
  els.vram.value = 0;
  els.users.value = 1;
  els.sort.value = "comfortableUsers";
  applyFilters();
}

function applyPreset(preset) {
  resetFilters();
  activePreset = preset;
  if (preset === "team") els.users.value = 5;
  if (preset === "lowLatency") els.sort.value = "peakAggregateTps";
  applyFilters();
}

async function importJson(file) {
  const text = await file.text();
  const data = JSON.parse(text);
  if (Array.isArray(data)) {
    allRuns = data;
  } else if (data.meta && data.summaries) {
    allRuns = [convertBenchmarkResult(data)];
  } else {
    throw new Error("Expected sample database array or benchmark results.json");
  }
  setupFilters();
  resetFilters();
}

function convertBenchmarkResult(result) {
  const config = result.meta?.benchmark_config || {};
  const hardware = result.meta?.gpu?.detected?.[0] || {};
  const runPoints = (result.summaries || []).map(summary => ({
    users: summary.concurrency,
    aggregateTps: summary.aggregate_output_tps || 0,
    perUserTps: summary.avg_per_request_tps || 0,
    ttft: summary.avg_ttft_s || 0,
    p95Latency: summary.p95_latency_s || 0,
    successRate: summary.requests ? summary.success / summary.requests * 100 : 0,
    vramUsedGb: null
  }));
  const peak = Math.max(0, ...runPoints.map(point => point.aggregateTps));
  const comfortable = Math.max(0, ...runPoints.filter(point => point.successRate === 100 && point.perUserTps >= 8).map(point => point.users));
  return {
    id: `import-${Date.now()}`,
    hardware: {
      brand: hardware.vendor || "Unknown",
      model: config.gpu_label || hardware.name || "Imported hardware",
      class: "GPU",
      vramGb: parseFloat(String(hardware.vram_total_human || "0")) || 0,
      memoryType: "",
      busWidth: null,
      boardPartner: "",
      priceUsd: null
    },
    system: {
      os: result.meta?.os?.system || "Unknown",
      cpu: result.meta?.cpu?.processor || "Unknown",
      ramGb: parseFloat(String(result.meta?.memory?.total_human || "0")) || 0
    },
    software: {
      runtime: config.server || "Unknown",
      backend: config.runtime_label || "Unknown",
      driver: "",
      endpoint: config.base_url || ""
    },
    model: {
      family: String(config.model || "Unknown").split(/[\\s:-]/)[0],
      name: config.model || "Unknown",
      sizeB: parseFloat(String(config.model || "").match(/(\\d+(?:\\.\\d+)?)\\s*b/i)?.[1] || "0"),
      quantization: config.model_quantization || "Unknown",
      format: "Unknown",
      context: config.context_size || 0
    },
    benchmark: {
      maxTokens: config.max_tokens_per_request || 0,
      promptTokensAvg: 0,
      comfortableUsers: comfortable,
      peakAggregateTps: peak,
      bestConcurrency: runPoints.find(point => point.aggregateTps === peak)?.users || 0,
      pricePerComfortableUser: null,
      verified: "Imported",
      runPoints
    }
  };
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

document.addEventListener("input", event => {
  if (event.target.closest(".filters") || event.target === els.sort) applyFilters();
});

els.body.addEventListener("click", event => {
  const row = event.target.closest("tr[data-id]");
  if (!row) return;
  selectedId = row.dataset.id;
  render();
});

document.querySelectorAll("[data-preset]").forEach(button => {
  button.addEventListener("click", () => applyPreset(button.dataset.preset));
});

els.importBtn.addEventListener("click", () => els.importFile.click());
els.importFile.addEventListener("change", async event => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    await importJson(file);
  } catch (err) {
    alert(`Could not import file: ${err.message}`);
  } finally {
    event.target.value = "";
  }
});
els.resetBtn.addEventListener("click", resetFilters);

fetch("sample-data.json")
  .then(response => response.json())
  .then(data => {
    allRuns = data;
    setupFilters();
    resetFilters();
  })
  .catch(err => {
    els.body.innerHTML = `<tr><td colspan="9">Could not load sample data: ${escapeHtml(err.message)}</td></tr>`;
  });
