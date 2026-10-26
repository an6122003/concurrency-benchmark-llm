# AI Concurrent Benchmark Report

## Test Environment

| Field | Value |
|---|---|
| Date | 2026-10-26T10:57:24 |
| Host | Windows 11 (ARM64) |
| OS | Windows-11-10.0.28000-SP0 |
| Python | 3.13.17 (C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe) |
| CPU | NVIDIA RTX Spark N1X (6144-core GPU, 20-core CPU) (20 logical cores) |
| System RAM | 30.5 GB |
| Detected GPU | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU); NVIDIA NPU; NVIDIA NPU; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) |
| GPU VRAM | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 98304 MiB used 26842 MiB free 71449 MiB; NVIDIA NPU; NVIDIA NPU total unknown; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 4.0 GB |
| Manual GPU label | NVIDIA RTX Spark N1X (Blackwell, 6144 CUDA cores), 128 GB LPDDR5X unified, ASUS ProArt P16 |
| Server mode | lmstudio |
| Base URL | http://127.0.0.1:8099 |
| Runtime label | llama.cpp b11671 (CUDA 13, Windows on Arm) llama-server |
| Runtime label source | manual |
| Model | qwen3.8-27b |
| Quantization | UD-Q4_K_M |
| Quantization source | manual |
| Context size | 65536 |
| Context size source | manual |
| Max tokens/request | 300 |
| Temperature | 0.2 |
| Timeout | 900.0 s |
| Concurrency | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 |
| Cooldown | 1.0 s |
| Warmup requests | 2 |
| Warmup tokens/request | 128 |
| Prompt count | 3 |
| Prompts file | C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\qwen3.8-27b\suite\prompts\02_team_concurrency.txt |
| Notes | server: --host 127.0.0.1 --port 8099 --alias qwen3.8-27b -ngl 999 --fit off -fa on -c 65536 -np 32 --kv-unified -b 2048 -ub 2048 --no-cache-prompt --cache-ram 0 --jinja --no-webui --metrics --reasoning off |

## Raw GPU Probe

### GPU Probe 1

```text
{
  "vendor": "NVIDIA",
  "name": "NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU)",
  "vram_total_mib": 98304,
  "vram_used_mib": 26842,
  "vram_free_mib": 71449,
  "vram_total_human": "98304 MiB",
  "vram_used_human": "26842 MiB",
  "vram_free_human": "71449 MiB",
  "driver": "617.69",
  "performance_state": "P8",
  "temperature_c": 66,
  "power_draw_w": "1.96"
}
```

### GPU Probe 2

```text
{
  "vendor": "NVIDIA",
  "name": "NVIDIA NPU",
  "vram_total_mib": null,
  "vram_used_mib": null,
  "vram_free_mib": null,
  "vram_total_human": "",
  "vram_used_human": "",
  "vram_free_human": "",
  "driver": "617.69",
  "performance_state": "[N/A]",
  "temperature_c": 72,
  "power_draw_w": "0.00"
}
```

### GPU Probe 3

```text
{
  "vendor": "Windows",
  "name": "NVIDIA NPU",
  "vram_total_bytes": null,
  "vram_total_human": "unknown",
  "vram_source": "Win32_VideoController.AdapterRAM",
  "reported_adapter_ram_bytes": null,
  "reported_adapter_ram_human": "unknown",
  "driver": "32.0.16.1769",
  "pnp_device_id": "ACPI\\NVDA200A\\0",
  "source": "Win32_VideoController"
}
```

### GPU Probe 4

```text
{
  "vendor": "Windows",
  "name": "NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU)",
  "vram_total_bytes": 4293918720,
  "vram_total_human": "4.0 GB",
  "vram_source": "Win32_VideoController.AdapterRAM",
  "reported_adapter_ram_bytes": 4293918720,
  "reported_adapter_ram_human": "4.0 GB",
  "driver": "32.0.16.1769",
  "pnp_device_id": "PCI\\VEN_10DE&DEV_2E03&SUBSYS_14841043&REV_A1\\00000000002DB04800",
  "source": "Win32_VideoController"
}
```


## Benchmark Summary

| Users | Success | Wall time (s) | Aggregate tok/s | Avg latency (s) | P95 latency (s) | Avg TTFT (s) | TTFT source | Avg per-user tok/s |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | 1/1 | 20.22 | 14.84 | 20.21 | 20.21 | 0.32 | {"stream": 1} | 14.84 |
| 2 | 2/2 | 20.36 | 25.20 | 17.61 | 20.08 | 0.65 | {"stream": 2} | 14.54 |
| 3 | 3/3 | 22.07 | 36.70 | 19.99 | 22.06 | 0.84 | {"stream": 3} | 13.48 |
| 4 | 4/4 | 23.40 | 42.40 | 19.87 | 23.29 | 1.06 | {"stream": 4} | 12.43 |
| 5 | 5/5 | 25.75 | 51.65 | 23.27 | 25.75 | 1.19 | {"stream": 5} | 11.41 |
| 6 | 6/6 | 27.51 | 57.18 | 24.64 | 27.51 | 1.34 | {"stream": 6} | 10.60 |
| 7 | 7/7 | 29.96 | 63.76 | 27.59 | 29.96 | 1.52 | {"stream": 7} | 9.85 |
| 8 | 8/8 | 31.94 | 65.84 | 28.74 | 31.94 | 1.65 | {"stream": 8} | 9.10 |
| 9 | 9/9 | 35.44 | 69.08 | 32.51 | 35.43 | 1.76 | {"stream": 9} | 8.34 |
| 10 | 10/10 | 37.46 | 69.79 | 33.18 | 37.45 | 1.94 | {"stream": 10} | 7.85 |

## Reading The Numbers

- Aggregate tok/s shows total generated throughput for the whole server at that user count.
- Avg per-user tok/s is closer to what one person feels while all simulated users are active.
- TTFT is time to first token. Lower feels more responsive in chat.
- Keep max tokens, prompts, context size, and concurrency groups the same when comparing runs.
- Larger max-token values can increase measured tok/s because fixed request and first-token costs are spread across more generated tokens.
- A practical team limit is usually where per-user tok/s and latency still feel acceptable, not where the server first errors.