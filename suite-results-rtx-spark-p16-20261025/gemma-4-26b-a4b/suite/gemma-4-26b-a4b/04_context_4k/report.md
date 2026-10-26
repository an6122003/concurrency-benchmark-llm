# AI Concurrent Benchmark Report

## Test Environment

| Field | Value |
|---|---|
| Date | 2026-10-26T11:52:25 |
| Host | Windows 11 (ARM64) |
| OS | Windows-11-10.0.28000-SP0 |
| Python | 3.13.17 (C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe) |
| CPU | NVIDIA RTX Spark N1X (6144-core GPU, 20-core CPU) (20 logical cores) |
| System RAM | 30.5 GB |
| Detected GPU | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU); NVIDIA NPU; NVIDIA NPU; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) |
| GPU VRAM | NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 98304 MiB used 37745 MiB free 60546 MiB; NVIDIA NPU; NVIDIA NPU total unknown; NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU) total 4.0 GB |
| Manual GPU label | NVIDIA RTX Spark N1X (Blackwell, 6144 CUDA cores), 128 GB LPDDR5X unified, ASUS ProArt P16 |
| Server mode | lmstudio |
| Base URL | http://127.0.0.1:8099 |
| Runtime label | llama.cpp b11671 (CUDA 13, Windows on Arm) llama-server |
| Runtime label source | manual |
| Model | gemma-4-26b-a4b |
| Quantization | Q8_0 |
| Quantization source | manual |
| Context size | 65536 |
| Context size source | manual |
| Max tokens/request | 160 |
| Temperature | 0.2 |
| Timeout | 900.0 s |
| Concurrency | 1, 2 |
| Cooldown | 1.0 s |
| Warmup requests | 1 |
| Warmup tokens/request | 64 |
| Prompt count | 1 |
| Prompts file | C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\gemma-4-26b-a4b\suite\prompts\04_context_4k.txt |
| Notes | server: --host 127.0.0.1 --port 8099 --alias gemma-4-26b-a4b -ngl 999 --fit off -fa on -c 65536 -np 32 --kv-unified -b 2048 -ub 2048 --no-cache-prompt --cache-ram 0 --jinja --no-webui --metrics --reasoning off |

## Raw GPU Probe

### GPU Probe 1

```text
{
  "vendor": "NVIDIA",
  "name": "NVIDIA RTX Spark N1X (6144-core Blackwell RTX GPU)",
  "vram_total_mib": 98304,
  "vram_used_mib": 37745,
  "vram_free_mib": 60546,
  "vram_total_human": "98304 MiB",
  "vram_used_human": "37745 MiB",
  "vram_free_human": "60546 MiB",
  "driver": "617.69",
  "performance_state": "P8",
  "temperature_c": 63,
  "power_draw_w": "1.87"
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
  "temperature_c": 66,
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
| 1 | 1/1 | 6.45 | 24.82 | 6.44 | 6.44 | 2.06 | {"stream": 1} | 24.85 |
| 2 | 2/2 | 10.79 | 29.65 | 10.73 | 10.78 | 3.61 | {"stream": 2} | 14.91 |

## Reading The Numbers

- Aggregate tok/s shows total generated throughput for the whole server at that user count.
- Avg per-user tok/s is closer to what one person feels while all simulated users are active.
- TTFT is time to first token. Lower feels more responsive in chat.
- Keep max tokens, prompts, context size, and concurrency groups the same when comparing runs.
- Larger max-token values can increase measured tok/s because fixed request and first-token costs are spread across more generated tokens.
- A practical team limit is usually where per-user tok/s and latency still feel acceptable, not where the server first errors.