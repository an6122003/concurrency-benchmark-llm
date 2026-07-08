# AI Hardware Benchmark Database Plan

## Goal

Build a database that helps people compare AI hardware for local LLM serving, not just by peak tokens/sec but by the real experience: responsiveness, concurrent usability, memory headroom, cost, software stack, and model compatibility.

## Core Entities

### Hardware

- Hardware model: `Radeon Pro R9700 AI Top`, `RTX 5090`, `RTX 4090`, `M4 Max`
- Brand and board partner: AMD, NVIDIA, Apple, Intel, Gigabyte, ASUS
- Hardware class: GPU, integrated GPU, CPU, NPU, multi-GPU rig
- Architecture: RDNA, Blackwell, Ada, Apple Silicon, Xe
- VRAM or unified memory
- Memory type and bus width
- Peak bandwidth
- TDP / TBP
- PCIe generation and lanes
- Driver version
- Price at test time
- Region/currency

### System

- CPU
- System RAM
- OS and version
- Kernel/build version
- Motherboard/laptop model
- Power profile
- Cooling profile
- Multi-GPU topology

### Software Stack

- Runtime: Ollama, LM Studio, llama.cpp server, vLLM, exllamav2, TensorRT-LLM
- Backend: Vulkan, CUDA, ROCm, Metal, CPU
- Runtime version
- Server endpoint type: OpenAI-compatible, Ollama native
- Quantization/runtime library: GGUF, GPTQ, AWQ, EXL2, MLX
- Driver/runtime dependencies: CUDA version, ROCm version, Vulkan driver, Metal version

### Model

- Model family: Gemma, Qwen, Llama, Mistral, DeepSeek, Phi
- Model name
- Parameter count
- Quantization
- File format
- Context size
- Prompt length
- Output length
- Vision/multimodal support
- Tool/function calling support

### Benchmark Run

- Run ID
- Date
- Submitter/source
- Hardware ID
- System ID
- Software stack ID
- Model ID
- Benchmark config
- Raw `results.json`
- Metadata JSON
- Notes
- Verification status

## Benchmark Scores To Collect

### Chat Serving

This is the core benchmark for team-shared local AI.

- Concurrent users: 1, 2, 3, 4, 5, 8, 10, 16
- Prompt tokens
- Generated tokens
- Aggregate output tok/s
- Average per-user tok/s
- Min/max per-user tok/s
- Time to first token
- P50/P95 latency
- Success rate
- Error rate
- Queueing behavior

Useful derived scores:

- Comfortable users: highest user count where success is 100%, avg per-user tok/s stays above target, and P95 latency is acceptable
- Peak throughput users: user count where aggregate tok/s peaks
- Responsiveness score: TTFT and P95 latency weighted score
- Fairness score: min per-user tok/s divided by average per-user tok/s

### Context Scaling

Tests how performance changes with larger prompts/context.

- Context sizes: 2K, 4K, 8K, 16K, 32K, 64K when supported
- Prefill tok/s
- Decode tok/s
- VRAM used
- Success/failure
- Context overflow behavior

Derived scores:

- Max practical context
- Context efficiency: tok/s per GB at each context size

### Model Scaling

Tests hardware across model sizes.

- Small: 3B-8B
- Medium: 9B-14B
- Large: 27B-34B
- XL: 70B+
- Quantizations: Q4, Q5, Q6, Q8, FP16 where possible

Derived scores:

- Largest fully-offloaded model
- Largest usable model
- Model-size efficiency: tok/s per billion parameters

### Memory Headroom

Records whether a setup is stable with real context and concurrent sessions.

- VRAM total
- VRAM used after load
- VRAM used during run
- KV cache growth
- Spill/offload behavior
- System RAM usage

Derived scores:

- VRAM headroom after load
- VRAM headroom at each concurrency level

### Cost And Efficiency

Important for buyers and teams.

- Hardware price
- Full system estimated price
- Wall power during idle/load if available
- Tokens/sec per dollar
- Comfortable users per dollar
- Tokens/sec per watt

### Single-Stream Responsiveness

The "how does it feel for one person" benchmark, separate from concurrency.

- 1-user decode tok/s
- 1-user TTFT (streamed)
- Cold-start time: model load to first token after server restart
- Warm TTFT vs cold TTFT

Derived scores:

- Snappiness score: TTFT under 0.5s and decode above reading speed (~12 tok/s)

### Batch / Offline Throughput

For data-processing workloads (summarize a folder, embeddings, agents) where
latency does not matter but total throughput does.

- Max aggregate tok/s at high concurrency (8-32 requests)
- Requests per minute at fixed prompt/output sizes
- Tokens per hour sustained over 10+ minutes

### Sustained Load And Stability

Peak numbers can hide thermal throttling and memory leaks.

- Aggregate tok/s in minute 1 vs minute 10 of continuous load
- Throttle ratio: sustained tok/s divided by peak tok/s
- Temperature and clock behavior if available
- VRAM growth over a long session (leak detection)
- Error rate over 100+ consecutive requests

### Prefill vs Decode Split

Prompt processing and generation stress hardware differently; both matter.

- Prefill tok/s at 1K/8K/32K prompt
- Decode tok/s at the same context depths
- Useful for RAG-heavy vs chat-heavy buying decisions

### Energy And Noise

- Wall power at idle, single-stream, and saturated load
- Tokens per joule (tok/s per watt)
- Energy per 1M output tokens

### Quality Sanity Checks

Performance alone can be misleading if a model is too small or too heavily quantized.

- Basic instruction following
- Summarization
- Coding
- Vietnamese answer quality
- Long-context retrieval sanity

These should be small fixed test sets, not a replacement for full evals.

## Recommended Filter System

### Primary Filters

- Hardware brand
- Hardware model
- VRAM / unified memory range
- Hardware class
- Model family
- Model size bucket
- Quantization
- Runtime
- Backend
- OS
- Concurrent user count

### Smart Filters

- "Best for 2-5 person team"
- "Best under $1,000"
- "Runs 30B fully on VRAM"
- "Best Vulkan results"
- "Best Ollama results"
- "Low TTFT"
- "High context"
- "Highest tok/s per dollar"
- "Laptop / small form factor"
- "No NVIDIA/CUDA required"

### Sorting

- Comfortable users
- Aggregate tok/s
- Per-user tok/s at selected concurrency
- P95 latency
- TTFT
- VRAM headroom
- Price/performance
- Efficiency per watt
- Date tested

## Data Quality Levels

- Verified: raw result JSON, metadata, software versions, and reproducible command are present
- Community: submitted with partial metadata
- Estimated: missing important metadata or inferred from public data
- Archived: old drivers/runtime/model version

## Implementation Status

The minimal first version below is implemented in this repo:

- `server/db.py`: SQLite schema — `hardware`, `systems`, `software`, `models`
  dimension tables, `runs` fact table with derived scores, and `run_points`
  per-concurrency measurements. Derived scores computed at import time:
  comfortable users, max success users, peak aggregate tok/s, best
  concurrency, 1-user tok/s, 1-user TTFT, price per comfortable user,
  tok/s per dollar, fairness score.
- `server/importer.py`: CLI importer for `results.json` files, run folders,
  suite folders, and database-format JSON.
- `server/app.py`: zero-dependency HTTP backend — `GET /api/runs` (filters,
  presets, sorting), `GET /api/runs/{id}`, `GET /api/facets`, `GET
  /api/stats`, `POST /api/import` — and serves the `web/` frontend.
- `web/`: browsing frontend with facet filters, smart presets, sliders,
  sorting, charts, and detail view. Works API-backed or as a static page.

Not yet collected by the benchmark scripts (future work): sustained-load,
prefill/decode split, energy, cold-start, and quality sanity scores.

## Minimal First Version

Start with these fields:

- Hardware model, brand, VRAM
- Runtime, backend, OS
- Model name, size, quantization, context size
- Max tokens, prompt count
- Concurrent users
- Aggregate tok/s
- Avg per-user tok/s
- Avg TTFT
- P95 latency
- Success rate
- Comfortable users
- Price if known
- Result JSON link

