// Shared data layer for the benchmark database pages.
// Uses the backend API when available, otherwise falls back to sample-data.json.

const DB = (() => {
  let mode = null;          // "api" | "static"
  let staticRuns = null;

  const PRESETS = {
    team: run => (run.benchmark.comfortableUsers || 0) >= 5,
    thirtyB: run => (run.model.sizeB || 0) >= 27,
    budget: run => run.hardware.priceUsd !== null && run.hardware.priceUsd <= 1000,
    nonCuda: run => !(run.software.backend || "").toLowerCase().includes("cuda"),
    lowLatency: run => firstTtft(run) !== null && firstTtft(run) <= 0.75,
    highContext: run => (run.model.context || 0) >= 16384,
    valueKing: () => true
  };

  function firstTtft(run) {
    return run.benchmark.ttft1u ?? run.benchmark.runPoints?.[0]?.ttft ?? null;
  }

  async function detect() {
    if (mode) return mode;
    try {
      const response = await fetch("/api/facets");
      if (response.ok) {
        mode = "api";
        api.facetsData = await response.json();
        return mode;
      }
    } catch (err) { /* static */ }
    mode = "static";
    staticRuns = await (await fetch("sample-data.json")).json();
    return mode;
  }

  function staticFacets() {
    const count = path => {
      const counts = {};
      staticRuns.forEach(run => {
        const value = path(run);
        if (value) counts[value] = (counts[value] || 0) + 1;
      });
      return Object.entries(counts).sort().map(([value, n]) => ({ value, count: n }));
    };
    return {
      brand: count(r => r.hardware.brand),
      family: count(r => r.model.family),
      runtime: count(r => r.software.runtime),
      backend: count(r => r.software.backend),
      verified: count(r => r.benchmark.verified)
    };
  }

  function matches(run, f) {
    const haystack = [
      run.hardware.brand, run.hardware.model, run.model.family, run.model.name,
      run.model.quantization, run.software.runtime, run.software.backend,
      run.system.os, run.system.cpu
    ].join(" ").toLowerCase();
    return (!f.search || haystack.includes(f.search.toLowerCase())) &&
      (!f.brand || run.hardware.brand === f.brand) &&
      (!f.family || run.model.family === f.family) &&
      (!f.runtime || run.software.runtime === f.runtime) &&
      (!f.backend || run.software.backend === f.backend) &&
      (!f.verified || run.benchmark.verified === f.verified) &&
      (!f.preset || !PRESETS[f.preset] || PRESETS[f.preset](run));
  }

  function sortValue(run, key) {
    if (key === "value") return run.benchmark.pricePerComfortableUser;
    if (key === "ttft") return firstTtft(run);
    if (key === "tps_per_dollar") {
      if (run.benchmark.tpsPerDollar) return run.benchmark.tpsPerDollar;
      return run.hardware.priceUsd ? (run.benchmark.peakAggregateTps || 0) / run.hardware.priceUsd : null;
    }
    if (key === "peak_aggregate_tps") return run.benchmark.peakAggregateTps;
    if (key === "tested_at") return run.testedAt || "";
    return run.benchmark.comfortableUsers;
  }

  const api = {
    facetsData: null,

    async mode() { return detect(); },

    async facets() {
      await detect();
      return mode === "api" ? api.facetsData : staticFacets();
    },

    // filters: {search, brand, family, runtime, backend, verified, preset, sort, limit, offset}
    async runs(filters) {
      await detect();
      if (mode === "api") {
        const params = new URLSearchParams();
        for (const key of ["search", "brand", "family", "runtime", "backend", "verified", "preset", "sort"]) {
          if (filters[key]) params.set(key, filters[key]);
        }
        params.set("limit", filters.limit || 24);
        params.set("offset", filters.offset || 0);
        const payload = await (await fetch(`/api/runs?${params}`)).json();
        return payload; // {total, runs}
      }
      const ascending = ["value", "ttft"].includes(filters.sort);
      const all = staticRuns.filter(run => matches(run, filters));
      all.sort((a, b) => {
        const av = sortValue(a, filters.sort), bv = sortValue(b, filters.sort);
        if (av === null || av === undefined) return 1;
        if (bv === null || bv === undefined) return -1;
        return ascending ? (av < bv ? -1 : 1) : (av > bv ? -1 : 1);
      });
      const offset = filters.offset || 0;
      const limit = filters.limit || 24;
      return { total: all.length, runs: all.slice(offset, offset + limit) };
    },

    async run(id) {
      await detect();
      if (mode === "api") {
        const response = await fetch(`/api/runs/${encodeURIComponent(id)}`);
        if (!response.ok) return null;
        return response.json();
      }
      return staticRuns.find(run => run.id === id) || null;
    },

    async import(text) {
      await detect();
      if (mode !== "api") throw new Error("Importing needs the backend. Start it with: python server/app.py --seed");
      const response = await fetch("/api/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: text
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || `import failed (${response.status})`);
      }
      return response.json();
    }
  };

  return api;
})();

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

function fmtNum(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "–";
  return Number(value).toFixed(digits);
}

function fmtMoney(value) {
  if (value === null || value === undefined) return "–";
  return `$${Math.round(value).toLocaleString()}`;
}

/* Compare selection, persisted across pages */
const CompareSet = {
  key: "techies-compare-ids",
  get() {
    try { return JSON.parse(localStorage.getItem(this.key)) || []; } catch { return []; }
  },
  set(ids) { localStorage.setItem(this.key, JSON.stringify(ids.slice(0, 5))); },
  toggle(id) {
    const ids = this.get();
    const index = ids.indexOf(id);
    if (index >= 0) ids.splice(index, 1); else ids.push(id);
    this.set(ids);
    return this.get();
  },
  clear() { this.set([]); }
};
