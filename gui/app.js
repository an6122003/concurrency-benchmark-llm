const scenarioTemplates = [
  ["01_latency_single_user", "Short chat responsiveness and TTFT.", "short_chat", "1", 96],
  ["02_team_concurrency", "Shared team chat serving from 1 to 10 users.", "short_chat", "1-10", 300],
  ["03_peak_decode_long_output", "Longer output for sustained decode throughput.", "short_chat", "1,2,4", 1024],
  ["04_context_4k", "Approximate 4K-word context pressure test.", "context", "1,2", 160, 4000],
  ["05_context_8k", "Approximate 8K-word context pressure test.", "context", "1", 160, 8000],
  ["06_coding_smoke", "Coding-oriented practical prompts.", "coding", "1,2", 384],
  ["07_vietnamese_smoke", "Vietnamese explanation/content prompts.", "vietnamese", "1,2", 384],
  ["08_extraction_classification", "Structured extraction and classification prompts.", "classification", "1,4", 256]
];

const ids = ["mode", "server", "baseUrl", "model", "runtime", "gpu", "quantization", "contextSize", "hardwareImage", "outDir", "notes", "concurrency", "maxTokens", "temperature", "warmup"];
const el = Object.fromEntries(ids.map(id => [id, document.getElementById(id)]));
const commandEl = document.getElementById("command");
const scenariosEl = document.getElementById("scenarios");

function shellQuote(value) {
  const text = String(value ?? "");
  if (!text) return "''";
  if (/^[A-Za-z0-9_./:=,-]+$/.test(text)) return text;
  return "'" + text.replace(/'/g, "'\"'\"'") + "'";
}

function renderScenarios() {
  scenariosEl.innerHTML = scenarioTemplates.map(([name, desc], index) => `
    <label class="scenario">
      <input type="checkbox" data-scenario="${index}" checked>
      <span><strong>${name}</strong><span>${desc}</span></span>
    </label>
  `).join("");
}

function selectedScenarios() {
  return [...document.querySelectorAll("[data-scenario]:checked")].map(input => {
    const [name, description, prompt_set, concurrency, max_tokens, approx_prompt_words] = scenarioTemplates[Number(input.dataset.scenario)];
    const scenario = {
      name,
      description,
      prompt_set,
      concurrency,
      max_tokens,
      warmup: name.includes("latency") || name.includes("team") ? 2 : 1,
      warmup_tokens: name.includes("team") ? 128 : 96
    };
    if (approx_prompt_words) scenario.approx_prompt_words = approx_prompt_words;
    return scenario;
  });
}

function targetConfig() {
  return {
    name: `${el.gpu.value || "Hardware"} ${el.model.value || "Model"}`.trim(),
    server: el.server.value,
    base_url: el.baseUrl.value,
    model: el.model.value,
    runtime: el.runtime.value,
    gpu: el.gpu.value,
    quantization: el.quantization.value,
    context_size: Number(el.contextSize.value) || undefined,
    hardware_image: el.hardwareImage.value,
    notes: el.notes.value
  };
}

function suiteConfig() {
  return {
    suite_name: "techieslab-local-llm-suite",
    targets: [targetConfig()],
    scenarios: selectedScenarios()
  };
}

function singleCommand() {
  const parts = [
    "python", "ai_concurrent_benchmark.py",
    "--server", el.server.value,
    "--base-url", el.baseUrl.value,
    "--model", el.model.value,
    "--concurrency", el.concurrency.value,
    "--max-tokens", el.maxTokens.value,
    "--temperature", el.temperature.value,
    "--warmup", el.warmup.value,
    "--out-dir", el.outDir.value
  ];
  const optional = {
    "--runtime": el.runtime.value,
    "--gpu": el.gpu.value,
    "--quantization": el.quantization.value,
    "--context-size": el.contextSize.value,
    "--hardware-image": el.hardwareImage.value,
    "--notes": el.notes.value
  };
  for (const [flag, value] of Object.entries(optional)) {
    if (value) parts.push(flag, value);
  }
  return parts.map(shellQuote).join(" ");
}

function suiteCommand() {
  return `python benchmark_suite.py --config suite-config.generated.json --out-dir ${shellQuote(el.outDir.value)}`;
}

function renderCommand() {
  if (el.mode.value === "single") {
    commandEl.textContent = singleCommand();
  } else {
    commandEl.textContent = [
      "1. Download the generated suite config as suite-config.generated.json",
      "2. Run:",
      "",
      suiteCommand(),
      "",
      "Generated config preview:",
      JSON.stringify(suiteConfig(), null, 2)
    ].join("\n");
  }
}

async function copyCommand() {
  const text = el.mode.value === "single" ? singleCommand() : suiteCommand();
  await navigator.clipboard.writeText(text);
}

function downloadConfig() {
  const blob = new Blob([JSON.stringify(suiteConfig(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "suite-config.generated.json";
  a.click();
  URL.revokeObjectURL(url);
}

document.addEventListener("input", renderCommand);
document.getElementById("copyCommand").addEventListener("click", copyCommand);
document.getElementById("downloadConfig").addEventListener("click", downloadConfig);
renderScenarios();
renderCommand();
