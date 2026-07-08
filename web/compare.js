// Compare page: overlaid per-metric charts + spec table for selected runs.

const content = document.getElementById("content");

Chart.defaults.color = "rgba(255,255,255,.72)";
Chart.defaults.borderColor = "rgba(255,255,255,.08)";

const COLORS = ["#8070f8", "#58c8f8", "#60d8c0", "#f8a860", "#f870c8"];

const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index", intersect: false },
  plugins: { legend: { position: "bottom" } }
};

function label(run) {
  return `${run.hardware.model} · ${run.model.sizeB ? run.model.sizeB + "B" : run.model.name}`;
}

function idsFromPage() {
  const fromUrl = (new URLSearchParams(location.search).get("ids") || "")
    .split(",").map(decodeURIComponent).filter(Boolean);
  return fromUrl.length ? fromUrl : CompareSet.get();
}

function metricChart(canvasId, runs, pointKey, yTitle) {
  new Chart(document.getElementById(canvasId), {
    type: "line",
    data: {
      datasets: runs.map((run, index) => ({
        label: label(run),
        data: (run.benchmark.runPoints || []).map(p => ({ x: p.users, y: p[pointKey] })),
        borderColor: COLORS[index % COLORS.length],
        backgroundColor: COLORS[index % COLORS.length],
        tension: .25,
        spanGaps: true
      }))
    },
    options: {
      ...commonOptions,
      scales: {
        x: { type: "linear", title: { display: true, text: "Concurrent users" }, ticks: { stepSize: 1 } },
        y: { title: { display: true, text: yTitle }, beginAtZero: true }
      }
    }
  });
}

function specRow(name, values, best) {
  const cells = values.map((v, i) => `<td class="${best !== null && i === best ? "best" : ""}">${v}</td>`).join("");
  return `<tr><th>${name}</th>${cells}</tr>`;
}

function bestIndex(values, higherIsBetter = true) {
  let best = null, bestValue = null;
  values.forEach((value, index) => {
    if (value === null || value === undefined) return;
    if (bestValue === null || (higherIsBetter ? value > bestValue : value < bestValue)) {
      bestValue = value; best = index;
    }
  });
  return best;
}

function render(runs) {
  const legend = runs.map((run, index) => `
    <span class="legend-chip">
      <i style="background:${COLORS[index % COLORS.length]}"></i>
      <a href="run.html?id=${encodeURIComponent(run.id)}">${escapeHtml(label(run))}</a>
      <button data-remove="${escapeHtml(run.id)}" title="Remove"><i data-lucide="x"></i></button>
    </span>
  `).join("");

  const b = key => runs.map(run => run.benchmark[key]);
  const ttfts = runs.map(run => run.benchmark.ttft1u ?? run.benchmark.runPoints?.[0]?.ttft ?? null);

  const table = `
    <div class="table-scroll">
    <table>
      <thead><tr><th></th>${runs.map((run, i) => `<th style="color:${COLORS[i % COLORS.length]}">${escapeHtml(run.hardware.model)}</th>`).join("")}</tr></thead>
      <tbody>
        ${specRow("Model", runs.map(run => `${escapeHtml(run.model.name)}${run.model.quantization ? ` · ${escapeHtml(run.model.quantization)}` : ""}`), null)}
        ${specRow("Stack", runs.map(run => `${escapeHtml(run.software.runtime)}${run.software.backend ? ` · ${escapeHtml(run.software.backend)}` : ""}`), null)}
        ${specRow("OS", runs.map(run => escapeHtml(run.system.os)), null)}
        ${specRow("VRAM", runs.map(run => run.hardware.vramGb ? `${run.hardware.vramGb} GB` : "–"), bestIndex(runs.map(r => r.hardware.vramGb)))}
        ${specRow("Price", runs.map(run => fmtMoney(run.hardware.priceUsd)), bestIndex(runs.map(r => r.hardware.priceUsd), false))}
        ${specRow("Comfortable users", b("comfortableUsers").map(v => v ?? "–"), bestIndex(b("comfortableUsers")))}
        ${specRow("Peak aggregate tok/s", b("peakAggregateTps").map(v => fmtNum(v)), bestIndex(b("peakAggregateTps")))}
        ${specRow("1-user TTFT", ttfts.map(v => v !== null ? fmtNum(v, 2) + " s" : "–"), bestIndex(ttfts, false))}
        ${specRow("$ per comfortable user", b("pricePerComfortableUser").map(v => fmtMoney(v)), bestIndex(b("pricePerComfortableUser"), false))}
        ${specRow("tok/s per $", b("tpsPerDollar").map(v => v ? fmtNum(v, 3) : "–"), bestIndex(b("tpsPerDollar")))}
        ${specRow("Data quality", b("verified").map(v => escapeHtml(v || "Community")), null)}
      </tbody>
    </table>
    </div>
  `;

  content.innerHTML = `
    <div class="legend-row">${legend}</div>
    ${table}
    <div class="grid">
      <section class="panel wide"><h2>Aggregate Throughput vs Concurrent Users</h2><div class="chart"><canvas id="aggChart"></canvas></div></section>
      <section class="panel"><h2>Per-user tok/s</h2><div class="chart"><canvas id="perUserChart"></canvas></div></section>
      <section class="panel"><h2>Avg TTFT</h2><div class="chart"><canvas id="ttftChart"></canvas></div></section>
      <section class="panel"><h2>P95 Latency</h2><div class="chart"><canvas id="p95Chart"></canvas></div></section>
      <section class="panel"><h2>Success Rate</h2><div class="chart"><canvas id="successChart"></canvas></div></section>
    </div>
  `;

  metricChart("aggChart", runs, "aggregateTps", "Tokens/sec");
  metricChart("perUserChart", runs, "perUserTps", "Tokens/sec");
  metricChart("ttftChart", runs, "ttft", "Seconds");
  metricChart("p95Chart", runs, "p95Latency", "Seconds");
  metricChart("successChart", runs, "successRate", "Success %");

  content.querySelectorAll("[data-remove]").forEach(button => {
    button.addEventListener("click", () => {
      const ids = idsFromPage().filter(id => id !== button.dataset.remove);
      CompareSet.set(ids);
      location.search = ids.length ? `?ids=${ids.map(encodeURIComponent).join(",")}` : "";
    });
  });

  lucide.createIcons();
}

async function boot() {
  const ids = idsFromPage();
  if (ids.length < 2) {
    content.innerHTML = `
      <div class="error">
        Pick at least two runs to compare.<br>
        On the <a href="browse.html">database page</a>, use the <b>+</b> button on any card to add it here.
      </div>`;
    return;
  }
  const runs = (await Promise.all(ids.map(id => DB.run(id)))).filter(Boolean);
  if (runs.length < 2) {
    content.innerHTML = '<div class="error">Could not load the selected runs. <a href="browse.html">Back to the database</a>.</div>';
    return;
  }
  render(runs.slice(0, 5));
}

boot();
