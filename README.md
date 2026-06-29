# Local AI Concurrent User Benchmark

This repo contains a cross-platform Python script for benchmarking concurrent chat sessions against LM Studio or Ollama.

It is designed for video production: each run outputs raw data plus a readable report and graph.

## Requirements

- Python 3.9+
- LM Studio server or Ollama running locally or on another machine
- No required Python packages

## LM Studio

Start the LM Studio local server, load your model, then run:

```bash
python ai_concurrent_benchmark.py --server lmstudio --base-url http://localhost:1234 --model "your-model-id" --concurrency 1-10 --max-tokens 256
```

On Windows PowerShell:

```powershell
python .\ai_concurrent_benchmark.py --server lmstudio --base-url http://localhost:1234 --model "your-model-id" --concurrency 1-10 --max-tokens 256
```

## Ollama

Using Ollama's OpenAI-compatible endpoint:

```bash
python ai_concurrent_benchmark.py --server ollama --base-url http://localhost:11434 --model "gemma3:27b" --concurrency 1-10 --max-tokens 256
```

Using Ollama's native `/api/generate` endpoint:

```bash
python ai_concurrent_benchmark.py --server ollama-native --base-url http://localhost:11434 --model "gemma3:27b" --concurrency 1-10 --max-tokens 256
```

## Output

Each run creates a folder like `benchmark-results-20260629-210000` with:

- `report.html`: graph for the video
- `compare.html`: browser page for comparing multiple `results.json` files
- `report.md`: summary table and interpretation notes
- `results.csv`: spreadsheet-friendly results
- `results.json`: full raw data
- `metadata.json`: hardware, software, runtime, and benchmark configuration metadata

## HTML Charts

`report.html` includes multiple chart views:

- Aggregate throughput vs concurrent users
- Average per-user throughput vs concurrent users
- Min/average/max per-user speed bars
- Average and P95 latency
- Average and P95 time to first token
- Success rate

These are useful for deciding which number to show in the video. Aggregate tok/s is good for server capacity, while per-user tok/s and TTFT are better for the viewer-friendly "how usable does it feel?" story.

## Comparing Runs

Open `compare.html` in your browser and add `results.json` files from different benchmark folders. You can add them one by one, remove individual runs, or clear the comparison.

Example comparison ideas:

- Ollama vs LM Studio
- Vulkan vs another runtime
- 30B Q4 vs smaller model
- Different GPUs
- Different `--max-tokens` or context settings

The comparison page draws separate lines for each result file across aggregate tok/s, per-user tok/s, latency, TTFT, and success rate. It also shows runtime, GPU, max-token, and context-size columns when that metadata exists.

## Useful Options

```bash
python ai_concurrent_benchmark.py \
  --server lmstudio \
  --base-url http://192.168.1.10:1234 \
  --model "gemma-3-27b-it-q4_k_m" \
  --concurrency 1,2,3,4,5,6,7,8,9,10 \
  --max-tokens 300 \
  --context-size 8192 \
  --temperature 0.2 \
  --runtime "Vulkan llama.cpp" \
  --gpu "Radeon Pro R9700 32GB" \
  --quantization "Q4_K_M" \
  --notes "Driver version, power limit, server settings, or filming notes" \
  --timeout 900 \
  --warmup 1 \
  --out-dir r9700-32gb-gemma-benchmark
```

`--concurrency` accepts ranges or lists:

- `1-10`
- `2-10`
- `1,2,5,10`

`--prompts-file` accepts either:

- A text file with one prompt per line
- A text file with prompts separated by `---`
- A JSON file containing a list of prompt strings

By default, the script sends one single-user warmup request before recording measured results. This avoids making the `users=1` score look artificially bad because of model loading, shader/kernel compilation, cache setup, or first-request server overhead. Warmup requests are stored in `results.json` under `warmup_requests`, but they are not included in the summary charts.

Warmup options:

- `--warmup 0`: disable warmup
- `--warmup 2`: send two warmup requests
- `--warmup-tokens 128`: generate more tokens during warmup
- `--warmup-pause 2`: wait two seconds after warmup before measuring

## Metadata In Reports

The script automatically records best-effort environment and server details:

- OS, platform, Python version, Python executable
- CPU name and logical core count
- System RAM
- GPU/card and VRAM information from common platform tools when available, including `nvidia-smi`, `rocm-smi`, macOS `system_profiler`, Windows video controller metadata, and Linux `lspci`
- Ollama version, model details, quantization, context metadata, and running-model info when using Ollama endpoints that expose it
- LM Studio model metadata from `/api/v0/models` when available, plus `/v1/models` as a basic OpenAI-compatible fallback
- Local process/model-file hints when `--base-url` points to `localhost`, `127.0.0.1`, `::1`, or `0.0.0.0`
- Benchmark settings such as server mode, base URL, model, max tokens, temperature, timeout, cooldown, prompt count, and concurrency groups

Metadata priority is:

1. API-provided metadata
2. Local environment scan for localhost servers
3. Manual flags as explicit overrides or cleaner labels

The local scan looks at running process command lines, common Ollama/LM Studio model folders, model filenames, and relevant environment variables. This can infer details such as `Q4_K_M`, context flags like `--ctx-size`, and runtime hints like Vulkan/CUDA/ROCm/Metal/llama.cpp when those strings are visible locally.

Some runtime details are still not exposed consistently by every server or every endpoint. Manual flags remain useful as explicit overrides/fallback labels for cases where neither the API nor local scan can provide the detail, or where you want cleaner labels in the video:

```bash
python ai_concurrent_benchmark.py \
  --server lmstudio \
  --base-url http://localhost:1234 \
  --model "gemma-3-27b-it-q4_k_m" \
  --runtime "Vulkan llama.cpp" \
  --gpu "Radeon Pro R9700 32GB" \
  --quantization "Q4_K_M" \
  --context-size 8192 \
  --max-tokens 300 \
  --concurrency 1-10
```

Those labels are written into `report.md`, `report.html`, `results.json`, `metadata.json`, and the comparison page.

On Windows, `Win32_VideoController.AdapterRAM` can under-report modern discrete GPU VRAM. The script tries a registry VRAM probe first and labels the source as `registry` when that value is available; otherwise it falls back to the Windows video controller value and records that source.

## Metrics For The Video

- **Aggregate tok/s**: total server output throughput at that user count.
- **Avg per-user tok/s**: what one simulated user roughly feels while everyone is active.
- **Avg latency**: total request time.
- **Avg TTFT**: time to first token, important for chat responsiveness.
- **Success count**: whether the server can actually handle every concurrent request.

TTFT source is recorded per request:

- `stream`: measured from the first streamed content chunk.
- `end_fallback`: the server returned content, but the client only saw it at the end, so this is closer to full-response latency than true TTFT.
- `missing`: the request succeeded but no generated content chunk was observed.

`--max-tokens` can change the measured token/sec. Larger values often increase average tok/s because fixed costs like request setup, prompt processing, scheduling, cache allocation, and first-token latency are spread across more generated tokens. Very large values can eventually reduce tok/s if the context/cache grows, memory pressure increases, or the server starts queueing harder. For fair comparisons, keep `--max-tokens`, prompts, context size, and concurrency list the same across runs.

A practical team-size estimate is the highest concurrency where:

- success is `N/N`
- avg per-user tok/s still feels acceptable
- avg TTFT is not frustrating
- latency does not explode compared with lower user counts

For a video conclusion, this is usually more honest than saying the GPU "supports" the first number where requests merely finish.
