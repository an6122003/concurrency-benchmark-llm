# AI Concurrent Benchmark Report

## Test Environment

| Field | Value |
|---|---|
| Date | 2026-10-26T11:59:58 |
| Host | Windows 11 (ARM64) |
| OS | Windows-11-10.0.28000-SP0 |
| Python | 3.13.17 (C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe) |
| CPU | NVIDIA RTX Spark N1X (6144-core GPU, 20-core CPU) (20 logical cores) |
| System RAM | 30.5 GB |
| Detected GPU | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU); NVIDIA NPU; NVIDIA NPU; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) |
| GPU VRAM | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 98304 MiB used 28565 MiB free 69726 MiB; NVIDIA NPU; NVIDIA NPU total unknown; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 4.0 GB |
| Manual GPU label | NVIDIA RTX Spark N1X (Blackwell, 6144 CUDA cores), 128 GB LPDDR5X unified, ASUS ProArt P16 |
| Server mode | lmstudio |
| Base URL | http://127.0.0.1:8099 |
| Runtime label | llama.cpp b11671 (CUDA 13, Windows on Arm) llama-server |
| Runtime label source | manual |
| Model | nemotron-3.5-nano-30b |
| Quantization | Q4_K_M |
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
| Prompts file | C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\nemotron-3.5-nano-30b\suite\prompts\02_team_concurrency.txt |
| Notes | server: --host 127.0.0.1 --port 8099 --alias nemotron-3.5-nano-30b -ngl 999 --fit off -fa on -c 65536 -np 32 --kv-unified -b 2048 -ub 2048 --no-cache-prompt --cache-ram 0 --jinja --no-webui --metrics --reasoning off |

## Raw GPU Probe

### GPU Probe 1

```text
{
  "vendor": "NVIDIA",
  "name": "NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU)",
  "vram_total_mib": 98304,
  "vram_used_mib": 28565,
  "vram_free_mib": 69726,
  "vram_total_human": "98304 MiB",
  "vram_used_human": "28565 MiB",
  "vram_free_human": "69726 MiB",
  "driver": "617.69",
  "performance_state": "P8",
  "temperature_c": 64,
  "power_draw_w": "1.84"
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
  "temperature_c": 69,
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
| 1 | 1/1 | 3.80 | 78.92 | 3.80 | 3.80 | 0.18 | {"stream": 1} | 79.05 |
| 2 | 2/2 | 4.83 | 89.70 | 3.83 | 4.73 | 0.35 | {"stream": 2} | 54.57 |
| 3 | 3/3 | 5.45 | 96.89 | 3.80 | 5.26 | 0.49 | {"stream": 3} | 43.34 |
| 4 | 4/4 | 7.07 | 118.13 | 5.28 | 7.07 | 0.50 | {"stream": 4} | 37.48 |
| 5 | 5/5 | 7.96 | 120.74 | 5.84 | 7.96 | 0.63 | {"stream": 5} | 31.07 |
| 6 | 6/6 | 8.95 | 122.90 | 6.70 | 8.95 | 0.85 | {"stream": 6} | 26.03 |
| 7 | 7/7 | 10.49 | 140.88 | 8.34 | 10.49 | 0.69 | {"stream": 7} | 24.46 |
| 8 | 8/8 | 11.09 | 141.12 | 8.52 | 11.08 | 0.79 | {"stream": 8} | 21.96 |
| 9 | 9/9 | 11.86 | 146.51 | 9.02 | 11.86 | 0.88 | {"stream": 9} | 20.53 |
| 10 | 10/10 | 12.35 | 157.70 | 9.06 | 12.34 | 0.77 | {"stream": 10} | 20.44 |

## Reading The Numbers

- Aggregate tok/s shows total generated throughput for the whole server at that user count.
- Avg per-user tok/s is closer to what one person feels while all simulated users are active.
- TTFT is time to first token. Lower feels more responsive in chat.
- Keep max tokens, prompts, context size, and concurrency groups the same when comparing runs.
- Larger max-token values can increase measured tok/s because fixed request and first-token costs are spread across more generated tokens.
- A practical team limit is usually where per-user tok/s and latency still feel acceptable, not where the server first errors.