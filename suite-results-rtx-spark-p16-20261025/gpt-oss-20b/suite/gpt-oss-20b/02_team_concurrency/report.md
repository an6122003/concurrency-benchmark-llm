# AI Concurrent Benchmark Report

## Test Environment

| Field | Value |
|---|---|
| Date | 2026-10-26T11:44:20 |
| Host | Windows 11 (ARM64) |
| OS | Windows-11-10.0.28000-SP0 |
| Python | 3.13.17 (C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe) |
| CPU | NVIDIA RTX Spark N1X (6144-core GPU, 20-core CPU) (20 logical cores) |
| System RAM | 30.5 GB |
| Detected GPU | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU); NVIDIA NPU; NVIDIA NPU; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) |
| GPU VRAM | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 98304 MiB used 16317 MiB free 81974 MiB; NVIDIA NPU; NVIDIA NPU total unknown; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 4.0 GB |
| Manual GPU label | NVIDIA RTX Spark N1X (Blackwell, 6144 CUDA cores), 128 GB LPDDR5X unified, ASUS ProArt P16 |
| Server mode | lmstudio |
| Base URL | http://127.0.0.1:8099 |
| Runtime label | llama.cpp b11671 (CUDA 13, Windows on Arm) llama-server |
| Runtime label source | manual |
| Model | gpt-oss-20b |
| Quantization | MXFP4 |
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
| Prompts file | C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\gpt-oss-20b\suite\prompts\02_team_concurrency.txt |
| Notes | server: --host 127.0.0.1 --port 8099 --alias gpt-oss-20b -ngl 999 --fit off -fa on -c 65536 -np 32 --kv-unified -b 2048 -ub 2048 --no-cache-prompt --cache-ram 0 --jinja --no-webui --metrics --reasoning-effort low |

## Raw GPU Probe

### GPU Probe 1

```text
{
  "vendor": "NVIDIA",
  "name": "NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU)",
  "vram_total_mib": 98304,
  "vram_used_mib": 16317,
  "vram_free_mib": 81974,
  "vram_total_human": "98304 MiB",
  "vram_used_human": "16317 MiB",
  "vram_free_human": "81974 MiB",
  "driver": "617.69",
  "performance_state": "P8",
  "temperature_c": 64,
  "power_draw_w": "1.72"
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
  "temperature_c": 70,
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
| 1 | 1/1 | 3.92 | 76.56 | 3.91 | 3.91 | 0.21 | {"stream": 1} | 76.77 |
| 2 | 2/2 | 4.82 | 100.10 | 4.08 | 4.74 | 0.31 | {"stream": 2} | 58.35 |
| 3 | 3/3 | 6.35 | 128.42 | 5.83 | 6.35 | 0.33 | {"stream": 3} | 46.47 |
| 4 | 4/4 | 7.79 | 146.03 | 7.44 | 7.79 | 0.36 | {"stream": 4} | 38.17 |
| 5 | 5/5 | 8.50 | 155.03 | 7.65 | 8.50 | 0.35 | {"stream": 5} | 34.29 |
| 6 | 6/6 | 9.26 | 167.36 | 8.12 | 9.25 | 0.31 | {"stream": 6} | 31.54 |
| 7 | 7/7 | 10.98 | 177.25 | 10.27 | 10.98 | 0.40 | {"stream": 7} | 27.03 |
| 8 | 8/8 | 11.94 | 180.53 | 10.89 | 11.93 | 0.41 | {"stream": 8} | 24.65 |
| 9 | 9/9 | 10.69 | 211.98 | 9.02 | 10.68 | 0.44 | {"stream": 9} | 27.84 |
| 10 | 10/10 | 11.19 | 251.58 | 10.44 | 11.18 | 0.45 | {"stream": 10} | 27.00 |

## Reading The Numbers

- Aggregate tok/s shows total generated throughput for the whole server at that user count.
- Avg per-user tok/s is closer to what one person feels while all simulated users are active.
- TTFT is time to first token. Lower feels more responsive in chat.
- Keep max tokens, prompts, context size, and concurrency groups the same when comparing runs.
- Larger max-token values can increase measured tok/s because fixed request and first-token costs are spread across more generated tokens.
- A practical team limit is usually where per-user tok/s and latency still feel acceptable, not where the server first errors.