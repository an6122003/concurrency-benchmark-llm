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

Open `compare.html` in your browser and select multiple `results.json` files from different benchmark folders.

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

## Metadata In Reports

The script automatically records best-effort environment details:

- OS, platform, Python version, Python executable
- CPU name and logical core count
- System RAM
- GPU information from common platform tools when available
- Ollama version when using an Ollama endpoint
- Benchmark settings such as server mode, base URL, model, max tokens, temperature, timeout, cooldown, prompt count, and concurrency groups

Some runtime details are not exposed consistently by LM Studio or Ollama, so you can label them manually:

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

## Metrics For The Video

- **Aggregate tok/s**: total server output throughput at that user count.
- **Avg per-user tok/s**: what one simulated user roughly feels while everyone is active.
- **Avg latency**: total request time.
- **Avg TTFT**: time to first token, important for chat responsiveness.
- **Success count**: whether the server can actually handle every concurrent request.

A practical team-size estimate is the highest concurrency where:

- success is `N/N`
- avg per-user tok/s still feels acceptable
- avg TTFT is not frustrating
- latency does not explode compared with lower user counts

For a video conclusion, this is usually more honest than saying the GPU "supports" the first number where requests merely finish.
