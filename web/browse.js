// Browse page: search + preset chips + filter row + card grid + load more.

const PAGE_SIZE = 24;

const state = {
  search: "",
  brand: "", family: "", runtime: "", backend: "", verified: "",
  preset: "",
  sort: "comfortable_users",
  offset: 0
};

let loadedRuns = [];
let total = 0;

const els = {
  form: document.getElementById("searchForm"),
  search: document.getElementById("searchInput"),
  chips: document.getElementById("presetChips"),
  brand: document.getElementById("brandFilter"),
  family: document.getElementById("familyFilter"),
  runtime: document.getElementById("runtimeFilter"),
  backend: document.getElementById("backendFilter"),
  verified: document.getElementById("verifiedFilter"),
  reset: document.getElementById("resetBtn"),
  sort: document.getElementById("sortSelect"),
  grid: document.getElementById("cardGrid"),
  count: document.getElementById("resultCount"),
  title: document.getElementById("sectionTitle"),
  loadMore: document.getElementById("loadMore"),
  modeBadge: document.getElementById("modeBadge"),
  importBtn: document.getElementById("importBtn"),
  importFile: document.getElementById("importFile"),
  compareBar: document.getElementById("compareBar"),
  compareCount: document.getElementById("compareCount"),
  compareGo: document.getElementById("compareGo"),
  compareClear: document.getElementById("compareClear"),
  compareLink: document.getElementById("compareLink"),
  compareLinkCount: document.getElementById("compareLinkCount")
};

const PRESET_TITLES = {
  "": "Latest tested hardware",
  team: "Hardware for 2–5 person teams",
  thirtyB: "Runs 30B+ models",
  budget: "Best under $1,000",
  nonCuda: "No CUDA required",
  lowLatency: "Fastest first token",
  highContext: "High-context setups",
  valueKing: "Best tok/s per dollar"
};

function fillSelect(select, entries, label) {
  const current = select.value;
  select.innerHTML = [
    `<option value="">All ${label}</option>`,
    ...entries.map(e => `<option value="${escapeHtml(e.value)}">${escapeHtml(e.value)} (${e.count})</option>`)
  ].join("");
  select.value = current;
}

function verifiedBadge(run) {
  const label = run.benchmark.verified || "Community";
  return `<span class="badge ${escapeHtml(label.toLowerCase())}">${escapeHtml(label)}</span>`;
}

function hwIcon(run) {
  const cls = (run.hardware.class || "").toLowerCase();
  if (cls.includes("cpu")) return "cpu";
  if (cls.includes("integrated")) return "laptop";
  if (cls.includes("npu")) return "brain-circuit";
  return "microchip";
}

function cardHtml(run) {
  const bench = run.benchmark;
  const ttft = bench.ttft1u ?? bench.runPoints?.[0]?.ttft;
  const selected = CompareSet.get().includes(run.id);
  const vram = run.hardware.vramGb ? `${run.hardware.vramGb} GB` : "?";
  return `
    <a class="run-card" href="run.html?id=${encodeURIComponent(run.id)}">
      <div class="top">
        <div class="hw-icon"><i data-lucide="${hwIcon(run)}"></i></div>
        ${verifiedBadge(run)}
      </div>
      <h2>${escapeHtml(run.hardware.model)}</h2>
      <div class="spec">
        <b>Model</b> ${escapeHtml(run.model.name)}${run.model.quantization ? ` · ${escapeHtml(run.model.quantization)}` : ""}<br>
        <b>Stack</b> ${escapeHtml(run.software.runtime)}${run.software.backend ? ` · ${escapeHtml(run.software.backend)}` : ""}<br>
        <b>VRAM</b> ${vram}${run.hardware.priceUsd ? ` · ${fmtMoney(run.hardware.priceUsd)}` : ""}
      </div>
      <div class="nums">
        <div><span>Users</span><strong>${bench.comfortableUsers ?? "–"}</strong></div>
        <div><span>Peak tok/s</span><strong>${fmtNum(bench.peakAggregateTps)}</strong></div>
        <div><span>TTFT</span><strong>${ttft !== null && ttft !== undefined ? fmtNum(ttft, 2) + "s" : "–"}</strong></div>
      </div>
      <button class="compare-toggle ${selected ? "on" : ""}" data-compare="${escapeHtml(run.id)}" type="button"
              title="Add to compare"><i data-lucide="${selected ? "check" : "plus"}"></i></button>
    </a>
  `;
}

function renderGrid(append = false) {
  const html = loadedRuns.map(cardHtml).join("") ||
    '<div class="empty-grid">No runs match.<br>Try clearing filters, or import a results.json with the upload button.</div>';
  els.grid.innerHTML = html;
  els.count.textContent = total ? `${loadedRuns.length} of ${total} runs` : "";
  els.title.textContent = PRESET_TITLES[state.preset] || PRESET_TITLES[""];
  els.loadMore.hidden = loadedRuns.length >= total;
  lucide.createIcons();
}

async function query(append = false) {
  if (!append) state.offset = 0;
  const payload = await DB.runs({ ...state, limit: PAGE_SIZE, offset: state.offset });
  total = payload.total;
  loadedRuns = append ? loadedRuns.concat(payload.runs) : payload.runs;
  renderGrid(append);
}

function syncChips() {
  els.chips.querySelectorAll(".chip").forEach(chip => {
    chip.classList.toggle("active", chip.dataset.preset === state.preset);
  });
}

function renderCompareBar() {
  const ids = CompareSet.get();
  els.compareBar.hidden = ids.length === 0;
  els.compareCount.textContent = `${ids.length} run${ids.length === 1 ? "" : "s"} selected`;
  const href = `compare.html?ids=${ids.map(encodeURIComponent).join(",")}`;
  els.compareGo.href = href;
  els.compareLink.href = ids.length >= 2 ? href : "compare.html";
  els.compareLinkCount.textContent = ids.length ? `· ${ids.length} selected` : "· pick runs with the + button";
  lucide.createIcons();
}

/* ---------- events ---------- */

els.form.addEventListener("submit", event => {
  event.preventDefault();
  state.search = els.search.value.trim();
  query();
});

let searchTimer;
els.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.search = els.search.value.trim();
    query();
  }, 250);
});

els.chips.addEventListener("click", event => {
  const chip = event.target.closest("[data-preset]");
  if (!chip) return;
  state.preset = chip.dataset.preset;
  if (state.preset === "lowLatency") { state.sort = "ttft"; els.sort.value = "ttft"; }
  if (state.preset === "valueKing") { state.sort = "tps_per_dollar"; els.sort.value = "tps_per_dollar"; }
  syncChips();
  query();
});

[["brand", els.brand], ["family", els.family], ["runtime", els.runtime],
 ["backend", els.backend], ["verified", els.verified]].forEach(([key, select]) => {
  select.addEventListener("change", () => { state[key] = select.value; query(); });
});

els.sort.addEventListener("change", () => { state.sort = els.sort.value; query(); });

els.reset.addEventListener("click", () => {
  Object.assign(state, { search: "", brand: "", family: "", runtime: "", backend: "", verified: "", preset: "", sort: "comfortable_users" });
  els.search.value = "";
  [els.brand, els.family, els.runtime, els.backend, els.verified].forEach(select => { select.value = ""; });
  els.sort.value = "comfortable_users";
  syncChips();
  query();
});

els.loadMore.addEventListener("click", () => {
  state.offset += PAGE_SIZE;
  query(true);
});

els.grid.addEventListener("click", event => {
  const toggle = event.target.closest("[data-compare]");
  if (!toggle) return;
  event.preventDefault();
  event.stopPropagation();
  CompareSet.toggle(toggle.dataset.compare);
  const on = CompareSet.get().includes(toggle.dataset.compare);
  toggle.classList.toggle("on", on);
  toggle.innerHTML = `<i data-lucide="${on ? "check" : "plus"}"></i>`;
  renderCompareBar();
});

els.compareClear.addEventListener("click", () => {
  CompareSet.clear();
  renderCompareBar();
  renderGrid();
});

els.importBtn.addEventListener("click", () => els.importFile.click());
els.importFile.addEventListener("change", async event => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    await DB.import(await file.text());
    await boot(true);
  } catch (err) {
    alert(`Could not import: ${err.message}`);
  } finally {
    event.target.value = "";
  }
});

/* ---------- boot ---------- */

async function boot(refetchFacets = false) {
  const params = new URLSearchParams(location.search);
  if (params.get("preset") && state.preset === "" && !refetchFacets) state.preset = params.get("preset");
  if (params.get("search") && !refetchFacets) { state.search = params.get("search"); els.search.value = state.search; }
  if (params.get("sort") && !refetchFacets) { state.sort = params.get("sort"); els.sort.value = state.sort; }

  const mode = await DB.mode();
  els.modeBadge.textContent = mode === "api" ? "live database" : "static sample";

  if (refetchFacets) DB.facetsData = await (await fetch("/api/facets")).json();
  const facets = await DB.facets();
  fillSelect(els.brand, facets.brand || [], "brands");
  fillSelect(els.family, facets.family || [], "model families");
  fillSelect(els.runtime, facets.runtime || [], "runtimes");
  fillSelect(els.backend, facets.backend || [], "backends");
  fillSelect(els.verified, facets.verified || [], "quality levels");

  syncChips();
  renderCompareBar();
  await query();
}

boot();
