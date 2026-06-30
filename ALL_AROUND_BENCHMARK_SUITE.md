# All-Around Local LLM Benchmark Suite

This suite is designed for comparing local AI hardware across practical team-serving use cases, not just one peak tokens/sec number.

## Research Basis

- MLPerf Inference separates benchmark scenarios by deployment style, including Server, Offline, and SingleStream. For local AI hardware, this maps well to team-serving concurrency, batch/offline throughput, and single-user responsiveness.
- `llama-bench` separates prompt processing (`pp`), text generation (`tg`), and prompt-plus-generation (`pg`). For local LLM serving, this is the key split between prefill/context handling and decode speed.
- HELM and lm-evaluation-harness both emphasize repeatable scenarios, metrics, and task coverage. For this project, we use smaller practical task sets for smoke-quality review while keeping the main focus on hardware/runtime performance.

References:

- MLPerf Inference overview: https://docs.mlcommons.org/inference/index_gh/
- MLPerf Llama 2 70B scenarios: https://docs.mlcommons.org/inference/benchmarks/language/llama2-70b/
- llama.cpp `llama-bench`: https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md
- Stanford HELM: https://crfm.stanford.edu/helm/
- EleutherAI lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness

## Suite Sections

### 1. Single-User Responsiveness

Purpose: measure what one person feels when chatting.

Metrics:

- Time to first token
- End-to-end latency
- Output tok/s
- Prompt tokens
- Completion tokens

Recommended config:

- concurrency: `1`
- max tokens: `64-128`
- short prompts
- warmup: `2`

### 2. Team Concurrency

Purpose: estimate how many people can share one local AI server comfortably.

Metrics:

- Aggregate output tok/s
- Average per-user tok/s
- Min/max per-user tok/s
- TTFT
- P95 latency
- Success rate
- Comfortable users

Recommended config:

- concurrency: `1-10`, optionally `1,2,4,8,12,16`
- max tokens: `256-384`
- mixed practical prompts

### 3. Peak Decode / Long Output

Purpose: reduce fixed request overhead and expose sustained generation speed.

Metrics:

- Output tok/s
- Aggregate tok/s
- Latency
- Thermal/power stability if available

Recommended config:

- concurrency: `1,2,4`
- max tokens: `1024`
- short/medium prompt

Note: this score is often higher than short-chat tok/s because fixed overhead is amortized over more generated tokens.

### 4. Context Scaling / Prefill Pressure

Purpose: understand long-context behavior, KV cache growth, and prompt-processing pressure.

Metrics:

- Latency
- TTFT
- Success/failure
- VRAM used
- Output tok/s after long prompt

Recommended config:

- approximate prompt words: `2000`, `4000`, `8000`, optionally `16000`
- concurrency: `1`, optionally `1,2`
- max tokens: `128-192`

### 5. Model Scaling

Purpose: compare which model sizes a hardware setup can run comfortably.

Buckets:

- Small: 3B-8B
- Medium: 9B-14B
- Large: 27B-34B
- XL: 70B+

Metrics:

- Largest fully-offloaded model
- Largest usable model
- Tokens/sec per billion parameters
- VRAM headroom
- Success rate

### 6. Practical Task Smoke Tests

Purpose: keep performance comparisons grounded in real work.

Prompt sets:

- Vietnamese explanation
- Summarization
- Coding helper
- Classification/extraction
- Product/content brainstorming

Metrics:

- Performance metrics from the normal benchmark
- Optional human score: `bad`, `usable`, `good`, `excellent`
- Optional notes for hallucination, formatting, language quality

### 7. Cost And Efficiency

Purpose: help buyers understand value.

Metrics:

- Hardware price
- Full system price if known
- Comfortable users per dollar
- Tok/s per dollar
- Tok/s per watt if power is available

## Suggested Comparison Sheet Columns

- Suite name
- Scenario
- Hardware brand
- Hardware model
- VRAM
- CPU
- System RAM
- OS
- Runtime
- Backend
- Driver
- Model family
- Model name
- Parameter count
- Quantization
- Context size
- Max tokens
- Concurrent users
- Success rate
- Aggregate tok/s
- Avg per-user tok/s
- Avg TTFT
- P95 latency
- VRAM used
- Price
- Comfortable users
- Tok/s per dollar
- Notes
- Result JSON path

## Scoring Recommendation

Use separate scores instead of one universal score:

- **Responsiveness score**: TTFT + P95 latency
- **Team serving score**: comfortable users + per-user tok/s
- **Throughput score**: peak aggregate tok/s
- **Context score**: largest stable context and long-prompt latency
- **Value score**: comfortable users per dollar and tok/s per dollar
- **Compatibility score**: model sizes/quantizations that run without spill or failure

A single overall score can be useful for a leaderboard, but keep the subscores visible so people can choose based on their use case.

## Running The Suite

Edit `suite-config.example.json`, then run:

```bash
python benchmark_suite.py --config suite-config.example.json --out-dir suite-results-r9700
```

Dry run:

```bash
python benchmark_suite.py --config suite-config.example.json --dry-run
```

Output:

- Per-scenario benchmark folders
- `suite-manifest.json`
- `suite-comparison.csv`

