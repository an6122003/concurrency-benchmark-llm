// Run detail page — layout and charts follow the benchmark script's report.html.

const content = document.getElementById("content");
const compareBtn = document.getElementById("compareBtn");
const compareBtnText = document.getElementById("compareBtnText");

Chart.defaults.color = "rgba(255,255,255,.72)";
Chart.defaults.borderColor = "rgba(255,255,255,.08)";

const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index", intersect: false },
  plugins: { legend: { position: "bottom" } }
};

function statTile(label, value, accent = false) {
  if (value === null || value === undefined || value === "") return "";
  return `<div class="stat"><span>${escapeHtml(label)}</span><strong class="${accent ? "accent" : ""}">${value}</strong></div>`;
}

function render(run) {
  const bench = run.benchmark;
  const points = bench.runPoints || [];
  const hw = run.hardware, model = run.model, sw = run.software, sys = run.system;

  document.title = `${hw.model} · ${model.name} · Techies Lab Benchmarks`;

  const summaryRows = points.map(p => `
    <tr>
      <td>${p.users}</td>
      <td>${p.successRate !== null && p.successRate !== undefined ? fmtNum(p.successRate, 0) + "%" : "–"}</td>
      <td>${fmtNum(p.aggregateTps, 2)}</td>
      <td>${fmtNum(p.perUserTps, 2)}</td>
      <td>${fmtNum(p.minPerUserTps, 2)}</td>
      <td>${fmtNum(p.maxPerUserTps, 2)}</td>
      <td>${fmtNum(p.avgLatency, 2)}</td>
      <td>${fmtNum(p.p95Latency, 2)}</td>
      <td>${fmtNum(p.ttft, 2)}</td>
      <td>${p.vramUsedGb ? fmtNum(p.vramUsedGb, 1) + " GB" : "–"}</td>
    </tr>
  `).join("");

  content.innerHTML = `
    <h1>${escapeHtml(hw.model)} <em>×</em> ${escapeHtml(model.name)}</h1>
    <p class="meta">
      ${escapeHtml(hw.brand)} · ${escapeHtml(hw.class || "GPU")}${hw.vramGb ? ` · ${hw.vramGb} GB ${escapeHtml(hw.memoryType || "")}` : ""}
      <span class="badge">${escapeHtml(bench.verified || "Community")}</span><br>
      ${run.testedAt ? `Tested: ${escapeHtml(run.testedAt)} · ` : ""}${run.source ? `Source: ${escapeHtml(run.source)}` : ""}
    </p>

    <div class="stats">
      ${statTile("Comfortable users", bench.comfortableUsers ?? "–", true)}
      ${statTile("Peak aggregate tok/s", bench.peakAggregateTps ? `${fmtNum(bench.peakAggregateTps)} @ ${bench.bestConcurrency} users` : "–", true)}
      ${statTile("1-user tok/s", fmtNum(bench.singleUserTps ?? points[0]?.perUserTps))}
      ${statTile("1-user TTFT", bench.ttft1u !== null && bench.ttft1u !== undefined ? fmtNum(bench.ttft1u, 2) + " s" : (points[0]?.ttft ? fmtNum(points[0].ttft, 2) + " s" : null))}
      ${statTile("Runtime", `${escapeHtml(sw.runtime)}${sw.backend ? ` · ${escapeHtml(sw.backend)}` : ""}`)}
      ${statTile("Quantization", model.quantization ? escapeHtml(model.quantization) : null)}
      ${statTile("Context", model.context ? model.context.toLocaleString() : null)}
      ${statTile("Max tokens", bench.maxTokens)}
      ${statTile("Hardware price", hw.priceUsd ? fmtMoney(hw.priceUsd) : null)}
      ${statTile("$ per comfortable user", bench.pricePerComfortableUser ? fmtMoney(bench.pricePerComfortableUser) : null)}
      ${statTile("tok/s per $", bench.tpsPerDollar ? fmtNum(bench.tpsPerDollar, 3) : null)}
      ${statTile("Fairness", bench.fairnessScore ? fmtNum(bench.fairnessScore, 2) : null)}
    </div>

    <details>
      <summary>Full system and benchmark details</summary>
      <table class="meta-table"><tbody>
        <tr><th>Hardware</th><td>${escapeHtml(hw.brand)} ${escapeHtml(hw.model)}${hw.boardPartner ? ` (${escapeHtml(hw.boardPartner)})` : ""}</td></tr>
        ${hw.vramGb ? `<tr><th>VRAM</th><td>${hw.vramGb} GB ${escapeHtml(hw.memoryType || "")}${hw.busWidth ? ` · ${hw.busWidth}-bit bus` : ""}</td></tr>` : ""}
        <tr><th>OS</th><td>${escapeHtml(sys.os)} ${escapeHtml(sys.osVersion || "")}</td></tr>
        ${sys.cpu ? `<tr><th>CPU</th><td>${escapeHtml(sys.cpu)}</td></tr>` : ""}
        ${sys.ramGb ? `<tr><th>System RAM</th><td>${sys.ramGb} GB</td></tr>` : ""}
        <tr><th>Runtime</th><td>${escapeHtml(sw.runtime)}${sw.runtimeVersion ? ` ${escapeHtml(sw.runtimeVersion)}` : ""}</td></tr>
        ${sw.backend ? `<tr><th>Backend</th><td>${escapeHtml(sw.backend)}</td></tr>` : ""}
        ${sw.driver ? `<tr><th>Driver</th><td>${escapeHtml(sw.driver)}</td></tr>` : ""}
        ${sw.endpoint ? `<tr><th>Endpoint</th><td>${escapeHtml(sw.endpoint)}</td></tr>` : ""}
        <tr><th>Model</th><td>${escapeHtml(model.name)} (${escapeHtml(model.family)}${model.sizeB ? `, ${model.sizeB}B` : ""})</td></tr>
        ${model.format ? `<tr><th>Format</th><td>${escapeHtml(model.format)}</td></tr>` : ""}
        ${run.notes ? `<tr><th>Notes</th><td>${escapeHtml(run.notes)}</td></tr>` : ""}
        <tr><th>Run ID</th><td>${escapeHtml(run.id)}</td></tr>
      </tbody></table>
    </details>

    ${run.raw ? `<details><summary>Raw result JSON</summary><pre>${escapeHtml(JSON.stringify(run.raw, null, 2))}</pre></details>` : ""}

    <div class="grid">
      <section class="panel wide"><h2>Throughput vs Concurrent Users</h2><div class="chart"><canvas id="throughputChart"></canvas></div></section>
      <section class="panel"><h2>Per-user Speed Range</h2><div class="chart"><canvas id="perUserChart"></canvas></div></section>
      <section class="panel"><h2>Latency and TTFT</h2><div class="chart"><canvas id="latencyChart"></canvas></div></section>
      <section class="panel"><h2>Success Rate</h2><div class="chart"><canvas id="successChart"></canvas></div></section>
      ${points.some(p => p.vramUsedGb) ? '<section class="panel"><h2>VRAM Used</h2><div class="chart"><canvas id="vramChart"></canvas></div></section>' : ""}
    </div>

    <div class="table-scroll">
    <table>
      <thead><tr><th>Users</th><th>Success</th><th>Aggregate tok/s</th><th>Avg per-user tok/s</th><th>Min per-user</th><th>Max per-user</th><th>Avg latency (s)</th><th>P95 latency (s)</th><th>Avg TTFT (s)</th><th>VRAM used</th></tr></thead>
      <tbody>${summaryRows}</tbody>
    </table>
    </div>
  `;

  drawCharts(points);
  lucide.createIcons();
}

function drawCharts(points) {
  const labels = points.map(p => p.users);
  const has = key => points.some(p => p[key] !== null && p[key] !== undefined);
  const series = key => points.map(p => p[key]);

  new Chart(document.getElementById("throughputChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Aggregate output tok/s", data: series("aggregateTps"), borderColor: "#8070f8", backgroundColor: "#8070f8", tension: .25 },
        { label: "Avg per-user tok/s", data: series("perUserTps"), borderColor: "#60d8c0", backgroundColor: "#60d8c0", tension: .25 }
      ]
    },
    options: { ...commonOptions, scales: {
      x: { title: { display: true, text: "Concurrent users" } },
      y: { title: { display: true, text: "Tokens/sec" }, beginAtZero: true }
    } }
  });

  const perUserSets = [{ label: "Avg per-user tok/s", data: series("perUserTps"), backgroundColor: "#60d8c0" }];
  if (has("minPerUserTps")) perUserSets.unshift({ label: "Min per-user tok/s", data: series("minPerUserTps"), backgroundColor: "#3a7f77" });
  if (has("maxPerUserTps")) perUserSets.push({ label: "Max per-user tok/s", data: series("maxPerUserTps"), backgroundColor: "#a8ecd9" });
  new Chart(document.getElementById("perUserChart"), {
    type: "bar",
    data: { labels, datasets: perUserSets },
    options: { ...commonOptions, scales: {
      x: { title: { display: true, text: "Concurrent users" } },
      y: { title: { display: true, text: "Tokens/sec" }, beginAtZero: true }
    } }
  });

  const latencySets = [];
  if (has("avgLatency")) latencySets.push({ label: "Avg latency", data: series("avgLatency"), borderColor: "#f87070", backgroundColor: "#f87070", tension: .25 });
  if (has("p95Latency")) latencySets.push({ label: "P95 latency", data: series("p95Latency"), borderColor: "#f8a860", backgroundColor: "#f8a860", tension: .25 });
  if (has("ttft")) latencySets.push({ label: "Avg TTFT", data: series("ttft"), borderColor: "#a090f8", backgroundColor: "#a090f8", tension: .25 });
  if (has("p95Ttft")) latencySets.push({ label: "P95 TTFT", data: series("p95Ttft"), borderColor: "#58c8f8", backgroundColor: "#58c8f8", tension: .25 });
  new Chart(document.getElementById("latencyChart"), {
    type: "line",
    data: { labels, datasets: latencySets },
    options: { ...commonOptions, scales: {
      x: { title: { display: true, text: "Concurrent users" } },
      y: { title: { display: true, text: "Seconds" }, beginAtZero: true }
    } }
  });

  new Chart(document.getElementById("successChart"), {
    type: "bar",
    data: { labels, datasets: [{ label: "Success rate %", data: series("successRate"), backgroundColor: "#58c8f8" }] },
    options: { ...commonOptions, scales: {
      x: { title: { display: true, text: "Concurrent users" } },
      y: { min: 0, max: 100, title: { display: true, text: "Success %" } }
    } }
  });

  const vramCanvas = document.getElementById("vramChart");
  if (vramCanvas) {
    new Chart(vramCanvas, {
      type: "bar",
      data: { labels, datasets: [{ label: "VRAM used (GB)", data: series("vramUsedGb"), backgroundColor: "#8070f8" }] },
      options: { ...commonOptions, scales: {
        x: { title: { display: true, text: "Concurrent users" } },
        y: { title: { display: true, text: "GB" }, beginAtZero: true }
      } }
    });
  }
}

function syncCompareBtn(id) {
  const on = CompareSet.get().includes(id);
  compareBtnText.textContent = on ? "In compare list" : "Add to compare";
  compareBtn.style.borderColor = on ? "rgba(96,216,192,.55)" : "";
  compareBtn.style.color = on ? "#60d8c0" : "";
}

async function boot() {
  const id = new URLSearchParams(location.search).get("id");
  if (!id) {
    content.innerHTML = '<div class="error">No run selected. <a href="browse.html" style="color:#a090f8">Back to the database</a>.</div>';
    return;
  }
  const run = await DB.run(id);
  if (!run) {
    content.innerHTML = `<div class="error">Run <code>${escapeHtml(id)}</code> was not found. <a href="browse.html" style="color:#a090f8">Back to the database</a>.</div>`;
    return;
  }
  render(run);
  syncCompareBtn(id);
  compareBtn.addEventListener("click", () => {
    CompareSet.toggle(id);
    syncCompareBtn(id);
  });
}

boot();
