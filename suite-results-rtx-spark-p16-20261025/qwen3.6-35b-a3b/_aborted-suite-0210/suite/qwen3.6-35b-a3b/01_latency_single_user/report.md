# AI Concurrent Benchmark Report

## Test Environment

| Field | Value |
|---|---|
| Date | 2026-10-26T02:10:28 |
| Host | Windows 11 (ARM64) |
| OS | Windows-11-10.0.28000-SP0 |
| Python | 3.13.17 (C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe) |
| CPU | ARMv8 (64-bit) Family 8 Model D87 Revision   1, NVIDIA (20 logical cores) |
| System RAM | unknown |
| Detected GPU | not detected |
| GPU VRAM | not detected |
| Manual GPU label | NVIDIA RTX Spark N1X (Blackwell, 6144 CUDA cores), 128 GB LPDDR5X unified, ASUS ProArt P16 |
| Server mode | lmstudio |
| Base URL | http://127.0.0.1:8099 |
| Runtime label | llama.cpp b11671 (CUDA 13, Windows on Arm) llama-server |
| Runtime label source | manual |
| Model | qwen3.6-35b-a3b |
| Quantization | UD-Q4_K_M |
| Quantization source | manual |
| Context size | 65536 |
| Context size source | manual |
| Max tokens/request | 96 |
| Temperature | 0.2 |
| Timeout | 900.0 s |
| Concurrency | 1 |
| Cooldown | 1.0 s |
| Warmup requests | 2 |
| Warmup tokens/request | 96 |
| Prompt count | 3 |
| Prompts file | C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\qwen3.6-35b-a3b\suite\prompts\01_latency_single_user.txt |
| Notes | server: --host 127.0.0.1 --port 8099 --alias qwen3.6-35b-a3b -ngl 999 --fit off -fa on -c 65536 -np 32 --kv-unified -b 2048 -ub 2048 --no-cache-prompt --cache-ram 0 --jinja --no-webui --metrics --reasoning off |

## Benchmark Summary

| Users | Success | Wall time (s) | Aggregate tok/s | Avg latency (s) | P95 latency (s) | Avg TTFT (s) | TTFT source | Avg per-user tok/s |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | 0/1 | 2.13 | - | - | - | - | {} | - |

## Reading The Numbers

- Aggregate tok/s shows total generated throughput for the whole server at that user count.
- Avg per-user tok/s is closer to what one person feels while all simulated users are active.
- TTFT is time to first token. Lower feels more responsive in chat.
- Keep max tokens, prompts, context size, and concurrency groups the same when comparing runs.
- Larger max-token values can increase measured tok/s because fixed request and first-token costs are spread across more generated tokens.
- A practical team limit is usually where per-user tok/s and latency still feel acceptable, not where the server first errors.