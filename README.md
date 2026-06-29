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

The comparison page draws separate lines for each result file across aggregate tok/s, per-user tok/s, latency, TTFT, and success rate.

## Useful Options

```bash
python ai_concurrent_benchmark.py \
  --server lmstudio \
  --base-url http://192.168.1.10:1234 \
  --model "gemma-3-27b-it-q4_k_m" \
  --concurrency 1,2,3,4,5,6,7,8,9,10 \
  --max-tokens 300 \
  --temperature 0.2 \
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
