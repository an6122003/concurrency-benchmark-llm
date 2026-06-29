#!/usr/bin/env python3
"""
Concurrent local AI server benchmark for LM Studio and Ollama.

Works on Windows, Linux, and macOS with Python 3.9+ and no required
third-party dependencies.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import html
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_PROMPTS = [
    "Explain the difference between local AI and cloud AI for a small content team in Vietnamese. Keep it practical.",
    "Write a short product brainstorming list for using a local LLM server in a marketing team.",
    "Summarize why VRAM capacity matters for running a 30B quantized language model locally.",
    "Classify these feedback items into bug, feature request, or praise: app slow, love the UI, need export to PDF.",
    "Draft a friendly Vietnamese answer to a teammate asking whether local AI can replace ChatGPT for daily work.",
    "Give five risks of sharing one local AI server among several users, with mitigation ideas.",
    "Explain tokens per second, time to first token, and end-to-end latency in simple terms.",
    "Create a short checklist for testing a local LLM server before a team starts using it.",
    "Write a concise comparison: local AI is like buying a car, cloud AI is like taking a ride-hailing service.",
    "Suggest a simple policy for fair usage when 5 people share the same local AI server.",
]


@dataclass
class RequestResult:
    concurrency: int
    user_id: int
    ok: bool
    status: Optional[int]
    error: str
    started_at: float
    ended_at: float
    ttft_s: Optional[float]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    chars: int
    response_preview: str

    @property
    def latency_s(self) -> float:
        return self.ended_at - self.started_at

    @property
    def output_tokens_per_s(self) -> Optional[float]:
        if not self.ok or not self.completion_tokens or self.latency_s <= 0:
            return None
        return self.completion_tokens / self.latency_s


@dataclass
class GroupSummary:
    concurrency: int
    requests: int
    success: int
    failures: int
    wall_time_s: float
    total_completion_tokens: int
    total_tokens: int
    aggregate_output_tps: Optional[float]
    avg_latency_s: Optional[float]
    p50_latency_s: Optional[float]
    p95_latency_s: Optional[float]
    avg_ttft_s: Optional[float]
    p50_ttft_s: Optional[float]
    p95_ttft_s: Optional[float]
    avg_per_request_tps: Optional[float]
    min_per_request_tps: Optional[float]
    max_per_request_tps: Optional[float]
    errors: List[str] = field(default_factory=list)


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[int(rank)]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def avg(values: List[float]) -> Optional[float]:
    return statistics.fmean(values) if values else None


def fmt(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def fmt_bytes(num_bytes: Optional[int]) -> str:
    if num_bytes is None:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024


def parse_int_maybe(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    match = re.search(r"\d+", text.replace(",", ""))
    return int(match.group(0)) if match else None


def run_probe(cmd: List[str], timeout: float = 3.0) -> Optional[str]:
    if not cmd or shutil.which(cmd[0]) is None:
        return None
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception:
        return None
    output = (completed.stdout or completed.stderr or "").strip()
    return output if output else None


def http_get_json(url: str, timeout: float = 3.0) -> Optional[Any]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def http_post_json_response(url: str, payload: Dict[str, Any], timeout: float = 3.0) -> Optional[Any]:
    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def read_linux_mem_total() -> Optional[int]:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except Exception:
        return None
    return None


def collect_cpu_info() -> Dict[str, Any]:
    cpu = {
        "processor": platform.processor() or "unknown",
        "machine": platform.machine() or "unknown",
        "physical_or_logical_cores": os.cpu_count(),
    }
    if platform.system() == "Darwin":
        brand = run_probe(["sysctl", "-n", "machdep.cpu.brand_string"])
        if brand:
            cpu["processor"] = brand
    elif platform.system() == "Windows":
        name = run_probe(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"])
        if name:
            cpu["processor"] = name
    elif platform.system() == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.lower().startswith("model name"):
                    cpu["processor"] = line.split(":", 1)[1].strip()
                    break
        except Exception:
            pass
    return cpu


def collect_memory_info() -> Dict[str, Any]:
    total: Optional[int] = None
    if platform.system() == "Linux":
        total = read_linux_mem_total()
    elif platform.system() == "Darwin":
        raw = run_probe(["sysctl", "-n", "hw.memsize"])
        total = int(raw) if raw and raw.isdigit() else None
    elif platform.system() == "Windows":
        raw = run_probe(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
        total = int(raw) if raw and raw.strip().isdigit() else None
    return {"total_bytes": total, "total_human": fmt_bytes(total)}


def collect_gpu_info() -> Dict[str, Any]:
    gpus: List[Dict[str, Any]] = []
    nvidia = run_probe([
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,memory.free,driver_version,pstate,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ])
    if nvidia:
        for line in nvidia.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) >= 8:
                total_mib = parse_int_maybe(parts[1])
                used_mib = parse_int_maybe(parts[2])
                free_mib = parse_int_maybe(parts[3])
                gpus.append({
                    "vendor": "NVIDIA",
                    "name": parts[0],
                    "vram_total_mib": total_mib,
                    "vram_used_mib": used_mib,
                    "vram_free_mib": free_mib,
                    "vram_total_human": f"{total_mib} MiB" if total_mib is not None else "",
                    "vram_used_human": f"{used_mib} MiB" if used_mib is not None else "",
                    "vram_free_human": f"{free_mib} MiB" if free_mib is not None else "",
                    "driver": parts[4],
                    "performance_state": parts[5],
                    "temperature_c": parse_int_maybe(parts[6]),
                    "power_draw_w": parts[7],
                })

    rocm = run_probe(["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--showdriverversion"])
    if rocm:
        name_match = re.search(r"(?:Card series|Card model|Marketing Name|GPU ID).*?:\s*(.+)", rocm, flags=re.IGNORECASE)
        total_match = re.search(r"(?:VRAM Total Memory|Total Memory).*?:\s*([0-9.]+)\s*([GMK]?i?B|bytes?)?", rocm, flags=re.IGNORECASE)
        used_match = re.search(r"(?:VRAM Total Used Memory|Used Memory).*?:\s*([0-9.]+)\s*([GMK]?i?B|bytes?)?", rocm, flags=re.IGNORECASE)
        gpus.append({
            "vendor": "AMD",
            "name": name_match.group(1).strip() if name_match else "",
            "vram_total_human": total_match.group(0).split(":", 1)[1].strip() if total_match else "",
            "vram_used_human": used_match.group(0).split(":", 1)[1].strip() if used_match else "",
            "source": "rocm-smi",
            "raw": rocm[:3000],
        })

    if platform.system() == "Darwin":
        sp = run_probe(["system_profiler", "SPDisplaysDataType"], timeout=8.0)
        if sp:
            chipset = re.search(r"Chipset Model:\s*(.+)", sp)
            cores = re.search(r"Total Number of Cores:\s*(.+)", sp)
            vram = re.search(r"VRAM.*?:\s*(.+)", sp)
            gpus.append({
                "vendor": "Apple/Other",
                "name": chipset.group(1).strip() if chipset else "",
                "gpu_cores": cores.group(1).strip() if cores else "",
                "vram_total_human": vram.group(1).strip() if vram else "unified memory",
                "source": "system_profiler SPDisplaysDataType",
                "raw": sp[:3000],
            })
    elif platform.system() == "Windows":
        ps = run_probe([
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | ConvertTo-Json -Compress",
        ])
        if ps:
            try:
                data = json.loads(ps)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    adapter_ram = parse_int_maybe(item.get("AdapterRAM")) if isinstance(item, dict) else None
                    gpus.append({
                        "vendor": "Windows",
                        "name": item.get("Name", "") if isinstance(item, dict) else "",
                        "vram_total_bytes": adapter_ram,
                        "vram_total_human": fmt_bytes(adapter_ram),
                        "driver": item.get("DriverVersion", "") if isinstance(item, dict) else "",
                        "source": "Win32_VideoController",
                    })
            except Exception:
                gpus.append({"vendor": "Windows", "source": "Win32_VideoController", "raw": ps[:3000]})
    elif platform.system() == "Linux":
        lspci = run_probe(["lspci"])
        if lspci:
            display_lines = [line for line in lspci.splitlines() if "vga" in line.lower() or "3d controller" in line.lower() or "display" in line.lower()]
            if display_lines:
                gpus.append({"vendor": "Linux", "source": "lspci", "raw": "\n".join(display_lines)[:2000]})

    return {"detected": gpus}


def extract_ollama_quantization(show_data: Any) -> Optional[str]:
    if not isinstance(show_data, dict):
        return None
    details = show_data.get("details") if isinstance(show_data.get("details"), dict) else {}
    model_info = show_data.get("model_info") if isinstance(show_data.get("model_info"), dict) else {}
    for key in ("quantization_level", "general.quantization_version"):
        value = details.get(key) or model_info.get(key)
        if value:
            return str(value)
    for key, value in model_info.items():
        if key.endswith(".quantization_level") and value:
            return str(value)
    return None


def extract_ollama_context_size(show_data: Any) -> Optional[int]:
    if not isinstance(show_data, dict):
        return None
    model_info = show_data.get("model_info") if isinstance(show_data.get("model_info"), dict) else {}
    parameters = show_data.get("parameters")
    for key, value in model_info.items():
        if key.endswith(".context_length") or key.endswith(".block_count"):
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    if isinstance(parameters, str):
        for line in parameters.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] in {"num_ctx", "ctx_size", "context_length"}:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    return None


def iter_model_dicts(data: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            for item in data["data"]:
                if isinstance(item, dict):
                    yield item
        elif isinstance(data.get("models"), list):
            for item in data["models"]:
                if isinstance(item, dict):
                    yield item
        else:
            yield data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item


def find_model_metadata(data: Any, model: str) -> Optional[Dict[str, Any]]:
    model_lower = model.lower()
    fallback: Optional[Dict[str, Any]] = None
    for item in iter_model_dicts(data):
        identifiers = [
            str(item.get(key, ""))
            for key in ("id", "model", "name", "path", "filename", "displayName")
            if item.get(key)
        ]
        if fallback is None:
            fallback = item
        if any(model_lower in identifier.lower() or identifier.lower() in model_lower for identifier in identifiers):
            return item
    return fallback


def find_nested_value(data: Any, wanted_keys: Iterable[str]) -> Optional[Any]:
    wanted = {key.lower() for key in wanted_keys}
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in wanted or any(token in key_lower for token in wanted):
                if isinstance(value, (str, int, float)) and value != "":
                    return value
            nested = find_nested_value(value, wanted)
            if nested is not None:
                return nested
    elif isinstance(data, list):
        for item in data:
            nested = find_nested_value(item, wanted)
            if nested is not None:
                return nested
    return None


def is_local_base_url(base_url: str) -> bool:
    try:
        host = urllib.parse.urlparse(base_url).hostname
    except Exception:
        return False
    return host in {None, "", "localhost", "127.0.0.1", "::1", "0.0.0.0"}


def collect_process_lines() -> List[str]:
    system = platform.system()
    if system == "Windows":
        output = run_probe([
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress",
        ], timeout=6.0)
        if not output:
            return []
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return [output]
        if isinstance(data, dict):
            data = [data]
        return [
            f"{item.get('ProcessId', '')} {item.get('Name', '')} {item.get('CommandLine', '')}".strip()
            for item in data
            if isinstance(item, dict)
        ]
    output = run_probe(["ps", "axo", "pid=,comm=,args="], timeout=4.0)
    return output.splitlines() if output else []


def collect_relevant_processes(server: str) -> List[Dict[str, str]]:
    keywords = ["ollama", "lm studio", "lmstudio", "llama", "vulkan", "cuda", "rocm", "metal"]
    if server.startswith("ollama"):
        keywords.extend(["ollama runner", "ollama_llama_server"])
    else:
        keywords.extend(["lm studio", "lmstudio", "lms"])
    processes = []
    for line in collect_process_lines():
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            processes.append({"command": line[:2000]})
    return processes[:30]


def detect_quantization_from_text(text: str) -> Optional[str]:
    patterns = [
        r"\bQ[2-8]_[A-Z0-9_]+(?:_[A-Z0-9]+)?\b",
        r"\bIQ[1-4]_[A-Z0-9_]+\b",
        r"\bF(?:16|32)\b",
        r"\bBF16\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0).upper()
    return None


def detect_context_from_text(text: str) -> Optional[int]:
    patterns = [
        r"(?:--ctx-size|--context-size|--n_ctx|--num_ctx|num_ctx)\s+(\d+)",
        r"(?:ctx(?:-size)?|context(?:_length|_size)?)[:=](\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
    return None


def detect_runtime_from_text(text: str) -> Optional[str]:
    lower = text.lower()
    runtime_bits = []
    if "vulkan" in lower:
        runtime_bits.append("Vulkan")
    if "cuda" in lower or "cublas" in lower:
        runtime_bits.append("CUDA")
    if "rocm" in lower or "hipblas" in lower:
        runtime_bits.append("ROCm")
    if "metal" in lower:
        runtime_bits.append("Metal")
    if "llama" in lower or "gguf" in lower:
        runtime_bits.append("llama.cpp")
    return " ".join(dict.fromkeys(runtime_bits)) if runtime_bits else None


def collect_local_model_files(model: str) -> List[str]:
    candidates: List[Path] = []
    home = Path.home()
    roots = [
        home / ".ollama" / "models",
        home / ".lmstudio" / "models",
        home / "Library" / "Application Support" / "LM Studio" / "models",
        Path(os.environ.get("OLLAMA_MODELS", "")) if os.environ.get("OLLAMA_MODELS") else None,
        Path(os.environ.get("LMSTUDIO_MODELS", "")) if os.environ.get("LMSTUDIO_MODELS") else None,
    ]
    model_tokens = [token.lower() for token in re.split(r"[^a-zA-Z0-9]+", model) if len(token) >= 3]
    for root in [r for r in roots if r]:
        if not root.exists():
            continue
        try:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                name = str(path).lower()
                if path.suffix.lower() in {".gguf", ".bin", ".safetensors"} or any(token in name for token in model_tokens):
                    candidates.append(path)
                    if len(candidates) >= 25:
                        return [str(p) for p in candidates]
        except Exception:
            continue
    return [str(p) for p in candidates]


def collect_local_runtime_probe(server: str, base_url: str, model: str) -> Dict[str, Any]:
    if not is_local_base_url(base_url):
        return {"enabled": False, "reason": "base_url is not localhost"}
    processes = collect_relevant_processes(server)
    model_files = collect_local_model_files(model)
    combined = "\n".join([model, *[p["command"] for p in processes], *model_files])
    return {
        "enabled": True,
        "processes": processes,
        "model_files": model_files,
        "detected_runtime": detect_runtime_from_text(combined),
        "detected_quantization": detect_quantization_from_text(combined),
        "detected_context_size": detect_context_from_text(combined),
        "env": {
            key: value
            for key, value in os.environ.items()
            if key.startswith(("OLLAMA", "LMSTUDIO", "LLAMA", "GGML", "CUDA", "HIP", "ROCR", "VULKAN"))
        },
    }


def collect_runtime_probe(server: str, base_url: str, model: str) -> Dict[str, Any]:
    runtime: Dict[str, Any] = {"server_mode": server, "base_url": base_url}
    normalized = normalize_base_url(base_url)
    if server.startswith("ollama"):
        runtime["ollama_version"] = http_get_json(f"{normalized}/api/version")
        runtime["ollama_show"] = http_post_json_response(f"{normalized}/api/show", {"model": model})
        runtime["ollama_running_models"] = http_get_json(f"{normalized}/api/ps")
        runtime["detected_quantization"] = extract_ollama_quantization(runtime.get("ollama_show"))
        runtime["detected_context_size"] = extract_ollama_context_size(runtime.get("ollama_show"))
    else:
        runtime["openai_models"] = http_get_json(f"{normalized}/v1/models")
        runtime["lmstudio_models"] = http_get_json(f"{normalized}/api/v0/models")
        model_meta = find_model_metadata(runtime.get("lmstudio_models"), model)
        runtime["lmstudio_selected_model"] = model_meta
        quantization = find_nested_value(model_meta, ["quantization", "quant", "q_type"])
        context_size = find_nested_value(model_meta, ["context_length", "context_size", "ctx", "n_ctx"])
        if quantization:
            runtime["detected_quantization"] = str(quantization)
        if context_size:
            try:
                runtime["detected_context_size"] = int(context_size)
            except (TypeError, ValueError):
                runtime["detected_context_size"] = str(context_size)
    runtime["local_scan"] = collect_local_runtime_probe(server, base_url, model)
    return runtime


def collect_environment_info(args: argparse.Namespace, concurrencies: List[int], prompt_count: int) -> Dict[str, Any]:
    runtime_probe = collect_runtime_probe(args.server, args.base_url, args.model)
    local_scan = runtime_probe.get("local_scan", {}) if isinstance(runtime_probe.get("local_scan"), dict) else {}
    detected_quantization = runtime_probe.get("detected_quantization") or local_scan.get("detected_quantization")
    detected_quantization_source = "api" if runtime_probe.get("detected_quantization") else ("local" if local_scan.get("detected_quantization") else "")
    detected_context_size = runtime_probe.get("detected_context_size") or local_scan.get("detected_context_size")
    detected_context_size_source = "api" if runtime_probe.get("detected_context_size") else ("local" if local_scan.get("detected_context_size") else "")
    detected_runtime = local_scan.get("detected_runtime")
    return {
        "date": dt.datetime.now().isoformat(timespec="seconds"),
        "host": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
        },
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "cpu": collect_cpu_info(),
        "memory": collect_memory_info(),
        "gpu": collect_gpu_info(),
        "runtime": runtime_probe,
        "benchmark_config": {
            "server": args.server,
            "base_url": args.base_url,
            "model": args.model,
            "runtime_label": args.runtime or detected_runtime,
            "runtime_label_source": "manual" if args.runtime else ("local" if detected_runtime else ""),
            "gpu_label": args.gpu,
            "model_quantization": args.quantization or detected_quantization,
            "model_quantization_source": "manual" if args.quantization else detected_quantization_source,
            "context_size": args.context_size or detected_context_size,
            "context_size_source": "manual" if args.context_size else detected_context_size_source,
            "max_tokens_per_request": args.max_tokens,
            "temperature": args.temperature,
            "timeout_seconds": args.timeout,
            "concurrency": concurrencies,
            "cooldown_seconds": args.cooldown,
            "warmup_requests": args.warmup,
            "warmup_max_tokens": args.warmup_tokens,
            "prompt_count": prompt_count,
            "prompts_file": args.prompts_file,
            "notes": args.notes,
        },
        "server": args.server,
        "base_url": args.base_url,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "concurrency": concurrencies,
    }


def flatten_metadata(meta: Dict[str, Any]) -> List[Tuple[str, str]]:
    config = meta.get("benchmark_config", {})
    cpu = meta.get("cpu", {})
    memory = meta.get("memory", {})
    runtime = meta.get("runtime", {})
    gpu_entries = meta.get("gpu", {}).get("detected", [])
    gpu_summary = "; ".join(
        entry.get("name") or entry.get("raw", "").splitlines()[0][:120] or entry.get("source", "detected GPU")
        for entry in gpu_entries
    ) or "not detected"
    gpu_vram_summary = "; ".join(
        " ".join(part for part in [
            entry.get("name") or entry.get("vendor") or "GPU",
            f"total {entry.get('vram_total_human')}" if entry.get("vram_total_human") else "",
            f"used {entry.get('vram_used_human')}" if entry.get("vram_used_human") else "",
            f"free {entry.get('vram_free_human')}" if entry.get("vram_free_human") else "",
        ] if part)
        for entry in gpu_entries
    ) or "not detected"
    rows = [
        ("Date", str(meta.get("date", ""))),
        ("Host", str(meta.get("host", ""))),
        ("OS", str(meta.get("os", {}).get("platform", ""))),
        ("Python", f"{meta.get('python', '')} ({meta.get('python_executable', '')})"),
        ("CPU", f"{cpu.get('processor', 'unknown')} ({cpu.get('physical_or_logical_cores', 'unknown')} logical cores)"),
        ("System RAM", str(memory.get("total_human", "unknown"))),
        ("Detected GPU", gpu_summary),
        ("GPU VRAM", gpu_vram_summary),
        ("Manual GPU label", str(config.get("gpu_label") or "")),
        ("Server mode", str(config.get("server", ""))),
        ("Base URL", str(config.get("base_url", ""))),
        ("Runtime label", str(config.get("runtime_label") or "")),
        ("Runtime label source", str(config.get("runtime_label_source") or "")),
        ("Ollama version", json.dumps(runtime.get("ollama_version", ""), ensure_ascii=False) if runtime.get("ollama_version") else ""),
        ("Model", str(config.get("model", ""))),
        ("Quantization", str(config.get("model_quantization") or "")),
        ("Quantization source", str(config.get("model_quantization_source") or "")),
        ("Context size", str(config.get("context_size") or "")),
        ("Context size source", str(config.get("context_size_source") or "")),
        ("Max tokens/request", str(config.get("max_tokens_per_request", ""))),
        ("Temperature", str(config.get("temperature", ""))),
        ("Timeout", f"{config.get('timeout_seconds', '')} s"),
        ("Concurrency", ", ".join(str(x) for x in config.get("concurrency", []))),
        ("Cooldown", f"{config.get('cooldown_seconds', '')} s"),
        ("Warmup requests", str(config.get("warmup_requests", ""))),
        ("Warmup tokens/request", str(config.get("warmup_max_tokens", ""))),
        ("Prompt count", str(config.get("prompt_count", ""))),
        ("Prompts file", str(config.get("prompts_file") or "")),
        ("Notes", str(config.get("notes") or "")),
    ]
    return rows


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def http_post_json(
    url: str,
    payload: Dict[str, Any],
    timeout: float,
    stream: bool,
) -> urllib.response.addinfourl:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "User-Agent": "ai-concurrent-benchmark/1.0",
        },
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=timeout)


def parse_openai_stream(resp: urllib.response.addinfourl) -> Tuple[str, Optional[Dict[str, Any]], int]:
    chunks: List[str] = []
    usage: Optional[Dict[str, Any]] = None
    event_count = 0
    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            continue
        event_count += 1
        if obj.get("usage"):
            usage = obj["usage"]
        for choice in obj.get("choices", []):
            delta = choice.get("delta") or {}
            text = delta.get("content")
            if text:
                chunks.append(text)
    return "".join(chunks), usage, event_count


def parse_ollama_stream(resp: urllib.response.addinfourl) -> Tuple[str, Optional[Dict[str, Any]], int]:
    chunks: List[str] = []
    usage: Dict[str, Any] = {}
    event_count = 0
    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_count += 1
        text = obj.get("response")
        if text:
            chunks.append(text)
        if obj.get("done"):
            usage = obj
            break
    return "".join(chunks), usage or None, event_count


def request_openai_compatible(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> Tuple[int, str, Optional[float], Optional[int], Optional[int], Optional[int], str]:
    url = f"{normalize_base_url(base_url)}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise and practical assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    first_token_at: Optional[float] = None
    started = time.perf_counter()
    with http_post_json(url, payload, timeout, stream=True) as resp:
        status = getattr(resp, "status", None) or resp.getcode()
        chunks: List[str] = []
        usage: Optional[Dict[str, Any]] = None
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            if obj.get("usage"):
                usage = obj["usage"]
            for choice in obj.get("choices", []):
                delta = choice.get("delta") or {}
                text = delta.get("content")
                if text:
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    chunks.append(text)
        output = "".join(chunks)
    prompt_tokens = usage.get("prompt_tokens") if usage else None
    completion_tokens = usage.get("completion_tokens") if usage else None
    total_tokens = usage.get("total_tokens") if usage else None
    if completion_tokens is None:
        completion_tokens = estimate_tokens(output)
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    ttft = first_token_at - started if first_token_at else None
    return status, output, ttft, prompt_tokens, completion_tokens, total_tokens, ""


def request_ollama_native(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> Tuple[int, str, Optional[float], Optional[int], Optional[int], Optional[int], str]:
    url = f"{normalize_base_url(base_url)}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    first_token_at: Optional[float] = None
    started = time.perf_counter()
    chunks: List[str] = []
    final_obj: Optional[Dict[str, Any]] = None
    with http_post_json(url, payload, timeout, stream=True) as resp:
        status = getattr(resp, "status", None) or resp.getcode()
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = obj.get("response")
            if text:
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                chunks.append(text)
            if obj.get("done"):
                final_obj = obj
                break
    output = "".join(chunks)
    completion_tokens = None
    prompt_tokens = None
    total_tokens = None
    if final_obj:
        completion_tokens = final_obj.get("eval_count")
        prompt_tokens = final_obj.get("prompt_eval_count")
    if completion_tokens is None:
        completion_tokens = estimate_tokens(output)
    if prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    ttft = first_token_at - started if first_token_at else None
    return status, output, ttft, prompt_tokens, completion_tokens, total_tokens, ""


def estimate_tokens(text: str) -> int:
    # Lightweight fallback when the server does not return token usage.
    return max(1, round(len(text) / 4))


def run_one(
    server: str,
    base_url: str,
    model: str,
    prompt: str,
    concurrency: int,
    user_id: int,
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> RequestResult:
    started_at = time.perf_counter()
    try:
        if server == "ollama-native":
            status, output, ttft, prompt_tokens, completion_tokens, total_tokens, err = request_ollama_native(
                base_url, model, prompt, max_tokens, temperature, timeout
            )
        else:
            status, output, ttft, prompt_tokens, completion_tokens, total_tokens, err = request_openai_compatible(
                base_url, model, prompt, max_tokens, temperature, timeout
            )
        ended_at = time.perf_counter()
        return RequestResult(
            concurrency=concurrency,
            user_id=user_id,
            ok=200 <= int(status) < 300,
            status=status,
            error=err,
            started_at=started_at,
            ended_at=ended_at,
            ttft_s=ttft,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            chars=len(output),
            response_preview=output[:240].replace("\n", " "),
        )
    except urllib.error.HTTPError as exc:
        ended_at = time.perf_counter()
        body = exc.read().decode("utf-8", errors="replace")[:500]
        return RequestResult(concurrency, user_id, False, exc.code, body, started_at, ended_at, None, None, None, None, 0, "")
    except Exception as exc:
        ended_at = time.perf_counter()
        return RequestResult(concurrency, user_id, False, None, repr(exc), started_at, ended_at, None, None, None, None, 0, "")


def summarize_group(concurrency: int, results: List[RequestResult], wall_time_s: float) -> GroupSummary:
    successes = [r for r in results if r.ok]
    latencies = [r.latency_s for r in successes]
    ttfts = [r.ttft_s for r in successes if r.ttft_s is not None]
    per_request_tps = [r.output_tokens_per_s for r in successes if r.output_tokens_per_s is not None]
    completion_tokens = sum(r.completion_tokens or 0 for r in successes)
    total_tokens = sum(r.total_tokens or 0 for r in successes)
    errors = sorted({r.error[:160] for r in results if not r.ok and r.error})
    aggregate_tps = completion_tokens / wall_time_s if wall_time_s > 0 and completion_tokens else None
    return GroupSummary(
        concurrency=concurrency,
        requests=len(results),
        success=len(successes),
        failures=len(results) - len(successes),
        wall_time_s=wall_time_s,
        total_completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        aggregate_output_tps=aggregate_tps,
        avg_latency_s=avg(latencies),
        p50_latency_s=percentile(latencies, 0.50),
        p95_latency_s=percentile(latencies, 0.95),
        avg_ttft_s=avg(ttfts),
        p50_ttft_s=percentile(ttfts, 0.50),
        p95_ttft_s=percentile(ttfts, 0.95),
        avg_per_request_tps=avg([x for x in per_request_tps if x is not None]),
        min_per_request_tps=min(per_request_tps) if per_request_tps else None,
        max_per_request_tps=max(per_request_tps) if per_request_tps else None,
        errors=errors,
    )


def parse_concurrency(spec: str) -> List[int]:
    values: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            start, end = int(left), int(right)
            step = 1 if end >= start else -1
            values.extend(range(start, end + step, step))
        else:
            values.append(int(part))
    unique = []
    for value in values:
        if value < 1:
            raise ValueError("Concurrency must be >= 1")
        if value not in unique:
            unique.append(value)
    return unique


def load_prompts(path: Optional[str]) -> List[str]:
    if not path:
        return DEFAULT_PROMPTS
    prompt_path = Path(path)
    text = prompt_path.read_text(encoding="utf-8")
    if prompt_path.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
            raise ValueError("Prompt JSON must be a list of strings")
        return data
    prompts = [block.strip() for block in text.split("\n---\n") if block.strip()]
    if not prompts:
        prompts = [line.strip() for line in text.splitlines() if line.strip()]
    return prompts


def run_warmup(args: argparse.Namespace, prompts: List[str]) -> List[RequestResult]:
    warmup_results: List[RequestResult] = []
    if args.warmup <= 0:
        return warmup_results
    print(f"Warmup: {args.warmup} request(s), not included in scores")
    for idx in range(args.warmup):
        result = run_one(
            args.server,
            args.base_url,
            args.model,
            prompts[idx % len(prompts)],
            0,
            idx + 1,
            args.warmup_tokens,
            args.temperature,
            args.timeout,
        )
        warmup_results.append(result)
        status = "ok" if result.ok else "failed"
        print(
            f"  warmup {idx + 1}/{args.warmup}: {status} "
            f"latency_s={fmt(result.latency_s)} ttft_s={fmt(result.ttft_s)} "
            f"tok_s={fmt(result.output_tokens_per_s)}"
        )
    if args.warmup_pause > 0:
        time.sleep(args.warmup_pause)
    print()
    return warmup_results


def write_csv(path: Path, results: List[RequestResult], summaries: List[GroupSummary]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "concurrency", "user_id", "ok", "status", "latency_s", "ttft_s", "completion_tokens", "total_tokens", "output_tps", "error"])
        for r in results:
            writer.writerow(["request", r.concurrency, r.user_id, r.ok, r.status, f"{r.latency_s:.4f}", fmt(r.ttft_s, 4), r.completion_tokens, r.total_tokens, fmt(r.output_tokens_per_s, 4), r.error])
        for s in summaries:
            writer.writerow(["summary", s.concurrency, "", s.success == s.requests, "", f"{s.wall_time_s:.4f}", fmt(s.avg_ttft_s, 4), s.total_completion_tokens, s.total_tokens, fmt(s.aggregate_output_tps, 4), " | ".join(s.errors)])


def write_markdown(path: Path, meta: Dict[str, Any], summaries: List[GroupSummary]) -> None:
    lines = [
        "# AI Concurrent Benchmark Report",
        "",
        "## Test Environment",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in flatten_metadata(meta):
        if value:
            lines.append(f"| {key} | {value.replace('|', '/')} |")
    if meta.get("gpu", {}).get("detected"):
        lines.extend(["", "## Raw GPU Probe", ""])
        for idx, gpu in enumerate(meta["gpu"]["detected"], start=1):
            lines.extend([
                f"### GPU Probe {idx}",
                "",
                "```text",
                json.dumps(gpu, indent=2, ensure_ascii=False),
                "```",
                "",
            ])
    lines.extend([
        "",
        "## Benchmark Summary",
        "",
        "| Users | Success | Wall time (s) | Aggregate tok/s | Avg latency (s) | P95 latency (s) | Avg TTFT (s) | Avg per-user tok/s |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for s in summaries:
        lines.append(
            f"| {s.concurrency} | {s.success}/{s.requests} | {fmt(s.wall_time_s)} | {fmt(s.aggregate_output_tps)} | "
            f"{fmt(s.avg_latency_s)} | {fmt(s.p95_latency_s)} | {fmt(s.avg_ttft_s)} | {fmt(s.avg_per_request_tps)} |"
        )
    lines.extend([
        "",
        "## Reading The Numbers",
        "",
        "- Aggregate tok/s shows total generated throughput for the whole server at that user count.",
        "- Avg per-user tok/s is closer to what one person feels while all simulated users are active.",
        "- TTFT is time to first token. Lower feels more responsive in chat.",
        "- Keep max tokens, prompts, context size, and concurrency groups the same when comparing runs.",
        "- Larger max-token values can increase measured tok/s because fixed request and first-token costs are spread across more generated tokens.",
        "- A practical team limit is usually where per-user tok/s and latency still feel acceptable, not where the server first errors.",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def chart_value(value: Optional[float]) -> Optional[float]:
    return round(value, 3) if value is not None else None


def write_html(path: Path, meta: Dict[str, Any], summaries: List[GroupSummary]) -> None:
    chart_data = {
        "labels": [s.concurrency for s in summaries],
        "aggregate": [chart_value(s.aggregate_output_tps) for s in summaries],
        "perUser": [chart_value(s.avg_per_request_tps) for s in summaries],
        "minPerUser": [chart_value(s.min_per_request_tps) for s in summaries],
        "maxPerUser": [chart_value(s.max_per_request_tps) for s in summaries],
        "avgLatency": [chart_value(s.avg_latency_s) for s in summaries],
        "p95Latency": [chart_value(s.p95_latency_s) for s in summaries],
        "avgTtft": [chart_value(s.avg_ttft_s) for s in summaries],
        "p95Ttft": [chart_value(s.p95_ttft_s) for s in summaries],
        "successRate": [chart_value((s.success / s.requests) * 100 if s.requests else None) for s in summaries],
    }
    rows = "\n".join(
        f"<tr><td>{s.concurrency}</td><td>{s.success}/{s.requests}</td><td>{fmt(s.wall_time_s)}</td>"
        f"<td>{fmt(s.aggregate_output_tps)}</td><td>{fmt(s.avg_per_request_tps)}</td><td>{fmt(s.min_per_request_tps)}</td>"
        f"<td>{fmt(s.max_per_request_tps)}</td><td>{fmt(s.avg_latency_s)}</td><td>{fmt(s.p95_latency_s)}</td>"
        f"<td>{fmt(s.avg_ttft_s)}</td></tr>"
        for s in summaries
    )
    meta_rows = "\n".join(
        f"<tr><th>{html.escape(key)}</th><td>{html.escape(value)}</td></tr>"
        for key, value in flatten_metadata(meta)
        if value
    )
    raw_meta = html.escape(json.dumps({
        "os": meta.get("os", {}),
        "cpu": meta.get("cpu", {}),
        "memory": meta.get("memory", {}),
        "gpu": meta.get("gpu", {}),
        "runtime": meta.get("runtime", {}),
        "benchmark_config": meta.get("benchmark_config", {}),
    }, indent=2, ensure_ascii=False))
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Concurrent Benchmark</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #161616; background: #fafafa; }}
    main {{ max-width: 1280px; margin: 0 auto; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: white; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
    th {{ background: #f3f3f3; }}
    td:first-child, th:first-child {{ text-align: left; }}
    .meta-table th {{ width: 220px; text-align: left; }}
    .meta-table td {{ text-align: left; }}
    .meta {{ color: #444; line-height: 1.5; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 18px; margin-top: 20px; }}
    .panel {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    .panel h2 {{ font-size: 18px; margin: 0 0 12px; }}
    .chart {{ height: 360px; }}
    .wide {{ grid-column: 1 / -1; }}
    details {{ margin-top: 20px; background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
    @media (max-width: 620px) {{ body {{ margin: 12px; }} .grid {{ grid-template-columns: 1fr; }} .chart {{ height: 300px; }} }}
  </style>
</head>
<body>
<main>
  <h1>AI Concurrent Benchmark</h1>
  <p class="meta">
    Date: {html.escape(meta['date'])}<br>
    Server: {html.escape(meta['benchmark_config']['server'])} at {html.escape(meta['benchmark_config']['base_url'])}<br>
    Model: {html.escape(meta['benchmark_config']['model'])}<br>
    Host: {html.escape(meta['host'])}
  </p>
  <table class="meta-table">
    <tbody>{meta_rows}</tbody>
  </table>
  <details>
    <summary>Raw detected hardware/software metadata</summary>
    <pre>{raw_meta}</pre>
  </details>
  <div class="grid">
    <section class="panel wide"><h2>Throughput vs Concurrent Users</h2><div class="chart"><canvas id="throughputChart"></canvas></div></section>
    <section class="panel"><h2>Per-user Speed Range</h2><div class="chart"><canvas id="perUserChart"></canvas></div></section>
    <section class="panel"><h2>Latency and TTFT</h2><div class="chart"><canvas id="latencyChart"></canvas></div></section>
    <section class="panel"><h2>Success Rate</h2><div class="chart"><canvas id="successChart"></canvas></div></section>
    <section class="panel"><h2>Latency Distribution</h2><div class="chart"><canvas id="latencyDistributionChart"></canvas></div></section>
  </div>
  <table>
    <thead><tr><th>Users</th><th>Success</th><th>Wall time (s)</th><th>Aggregate tok/s</th><th>Avg per-user tok/s</th><th>Min per-user tok/s</th><th>Max per-user tok/s</th><th>Avg latency (s)</th><th>P95 latency (s)</th><th>Avg TTFT (s)</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</main>
<script>
const data = {json.dumps(chart_data)};
const commonOptions = {{
  responsive: true,
  maintainAspectRatio: false,
  interaction: {{ mode: 'index', intersect: false }},
  plugins: {{ legend: {{ position: 'bottom' }} }}
}};

new Chart(document.getElementById('throughputChart'), {{
  type: 'line',
  data: {{
    labels: data.labels,
    datasets: [
      {{ label: 'Aggregate output tok/s', data: data.aggregate, borderColor: '#1f77b4', backgroundColor: '#1f77b4', tension: 0.25 }},
      {{ label: 'Avg per-user tok/s', data: data.perUser, borderColor: '#2ca02c', backgroundColor: '#2ca02c', tension: 0.25 }}
    ]
  }},
  options: {{
    ...commonOptions,
    scales: {{
      x: {{ title: {{ display: true, text: 'Concurrent users' }} }},
      y: {{ title: {{ display: true, text: 'Tokens/sec' }} }}
    }}
  }}
}});

new Chart(document.getElementById('perUserChart'), {{
  type: 'bar',
  data: {{
    labels: data.labels,
    datasets: [
      {{ label: 'Min per-user tok/s', data: data.minPerUser, backgroundColor: '#9edae5' }},
      {{ label: 'Avg per-user tok/s', data: data.perUser, backgroundColor: '#2ca02c' }},
      {{ label: 'Max per-user tok/s', data: data.maxPerUser, backgroundColor: '#98df8a' }}
    ]
  }},
  options: {{
    ...commonOptions,
    scales: {{
      x: {{ title: {{ display: true, text: 'Concurrent users' }} }},
      y: {{ title: {{ display: true, text: 'Tokens/sec' }} }}
    }}
  }}
}});

new Chart(document.getElementById('latencyChart'), {{
  type: 'line',
  data: {{
    labels: data.labels,
    datasets: [
      {{ label: 'Avg latency', data: data.avgLatency, borderColor: '#d62728', backgroundColor: '#d62728', tension: 0.25 }},
      {{ label: 'P95 latency', data: data.p95Latency, borderColor: '#ff7f0e', backgroundColor: '#ff7f0e', tension: 0.25 }},
      {{ label: 'Avg TTFT', data: data.avgTtft, borderColor: '#9467bd', backgroundColor: '#9467bd', tension: 0.25 }},
      {{ label: 'P95 TTFT', data: data.p95Ttft, borderColor: '#8c564b', backgroundColor: '#8c564b', tension: 0.25 }}
    ]
  }},
  options: {{
    ...commonOptions,
    scales: {{
      x: {{ title: {{ display: true, text: 'Concurrent users' }} }},
      y: {{ title: {{ display: true, text: 'Seconds' }} }}
    }}
  }}
}});

new Chart(document.getElementById('successChart'), {{
  type: 'bar',
  data: {{
    labels: data.labels,
    datasets: [{{ label: 'Success rate %', data: data.successRate, backgroundColor: '#17becf' }}]
  }},
  options: {{
    ...commonOptions,
    scales: {{
      x: {{ title: {{ display: true, text: 'Concurrent users' }} }},
      y: {{ min: 0, max: 100, title: {{ display: true, text: 'Success %' }} }}
    }}
  }}
}});

new Chart(document.getElementById('latencyDistributionChart'), {{
  type: 'bar',
  data: {{
    labels: data.labels,
    datasets: [
      {{ label: 'Avg latency', data: data.avgLatency, backgroundColor: '#ff9896' }},
      {{ label: 'P95 latency', data: data.p95Latency, backgroundColor: '#d62728' }}
    ]
  }},
  options: {{
    ...commonOptions,
    scales: {{
      x: {{ title: {{ display: true, text: 'Concurrent users' }} }},
      y: {{ title: {{ display: true, text: 'Seconds' }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def write_compare_html(path: Path) -> None:
    doc = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Benchmark Comparison</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; color: #161616; background: #fafafa; }
    main { max-width: 1280px; margin: 0 auto; }
    .toolbar { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 18px; margin-top: 20px; }
    .panel { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }
    .panel h2 { font-size: 18px; margin: 0 0 12px; }
    .chart { height: 360px; }
    .wide { grid-column: 1 / -1; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; background: white; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
    th { background: #f3f3f3; }
    td:first-child, th:first-child { text-align: left; }
    input { display: block; margin-top: 10px; }
    .hint { color: #555; line-height: 1.5; }
    @media (max-width: 620px) { body { margin: 12px; } .grid { grid-template-columns: 1fr; } .chart { height: 300px; } }
  </style>
</head>
<body>
<main>
  <h1>AI Benchmark Comparison</h1>
  <section class="toolbar">
    <strong>Select multiple <code>results.json</code> files</strong>
    <input id="files" type="file" accept=".json,application/json" multiple>
    <p class="hint">Use this to compare different GPUs, models, runtimes, quantizations, or server settings. The files stay in your browser.</p>
  </section>
  <div class="grid">
    <section class="panel wide"><h2>Aggregate Throughput</h2><div class="chart"><canvas id="aggregateChart"></canvas></div></section>
    <section class="panel"><h2>Average Per-user Speed</h2><div class="chart"><canvas id="perUserChart"></canvas></div></section>
    <section class="panel"><h2>Average Latency</h2><div class="chart"><canvas id="latencyChart"></canvas></div></section>
    <section class="panel"><h2>Average TTFT</h2><div class="chart"><canvas id="ttftChart"></canvas></div></section>
    <section class="panel"><h2>Success Rate</h2><div class="chart"><canvas id="successChart"></canvas></div></section>
  </div>
  <table id="summaryTable"></table>
</main>
<script>
const palette = ['#1f77b4', '#2ca02c', '#d62728', '#9467bd', '#ff7f0e', '#17becf', '#8c564b', '#e377c2'];
const charts = {};
const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: { legend: { position: 'bottom' } },
  scales: {
    x: { title: { display: true, text: 'Concurrent users' } },
    y: { beginAtZero: true }
  }
};

function runLabel(result, fallback) {
  const meta = result.meta || {};
  const config = meta.benchmark_config || {};
  const model = config.model || meta.model || 'unknown-model';
  const server = config.server || meta.server || 'server';
  const runtime = config.runtime_label ? ` ${config.runtime_label}` : '';
  const gpu = config.gpu_label ? ` ${config.gpu_label}` : '';
  const date = meta.date ? ' ' + meta.date.replace('T', ' ').slice(0, 16) : '';
  return `${model} (${server}${runtime}${gpu})${date}` || fallback;
}

function metric(summary, key) {
  if (key === 'success_rate') {
    return summary.requests ? (summary.success / summary.requests) * 100 : null;
  }
  return summary[key] ?? null;
}

function buildDatasets(runs, key) {
  return runs.map((run, index) => ({
    label: run.label,
    data: run.summaries.map(s => ({ x: s.concurrency, y: metric(s, key) })),
    borderColor: palette[index % palette.length],
    backgroundColor: palette[index % palette.length],
    tension: 0.25
  }));
}

function renderChart(id, runs, key, yTitle) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), {
    type: 'line',
    data: { datasets: buildDatasets(runs, key) },
    options: {
      ...commonOptions,
      parsing: false,
      scales: {
        x: { type: 'linear', title: { display: true, text: 'Concurrent users' }, ticks: { precision: 0 } },
        y: { beginAtZero: true, title: { display: true, text: yTitle } }
      }
    }
  });
}

function renderTable(runs) {
  const table = document.getElementById('summaryTable');
  if (!runs.length) {
    table.innerHTML = '';
    return;
  }
  const rows = [];
  rows.push('<thead><tr><th>Run</th><th>Runtime</th><th>GPU</th><th>Max tokens</th><th>Context</th><th>Users</th><th>Success</th><th>Aggregate tok/s</th><th>Avg per-user tok/s</th><th>Avg latency</th><th>Avg TTFT</th></tr></thead><tbody>');
  for (const run of runs) {
    const config = run.meta.benchmark_config || {};
    for (const s of run.summaries) {
      rows.push(`<tr><td>${escapeHtml(run.label)}</td><td>${escapeHtml(config.runtime_label || config.server || '')}</td><td>${escapeHtml(config.gpu_label || '')}</td><td>${escapeHtml(config.max_tokens_per_request ?? '')}</td><td>${escapeHtml(config.context_size ?? '')}</td><td>${s.concurrency}</td><td>${s.success}/${s.requests}</td><td>${fmt(s.aggregate_output_tps)}</td><td>${fmt(s.avg_per_request_tps)}</td><td>${fmt(s.avg_latency_s)}</td><td>${fmt(s.avg_ttft_s)}</td></tr>`);
    }
  }
  rows.push('</tbody>');
  table.innerHTML = rows.join('');
}

function fmt(value) {
  return value === null || value === undefined ? '-' : Number(value).toFixed(2);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

async function readFile(file) {
  const text = await file.text();
  const result = JSON.parse(text);
  return {
    label: runLabel(result, file.name),
    meta: result.meta || {},
    summaries: (result.summaries || []).slice().sort((a, b) => a.concurrency - b.concurrency)
  };
}

document.getElementById('files').addEventListener('change', async event => {
  const files = Array.from(event.target.files || []);
  const runs = [];
  for (const file of files) {
    try {
      runs.push(await readFile(file));
    } catch (err) {
      alert(`Could not read ${file.name}: ${err}`);
    }
  }
  renderChart('aggregateChart', runs, 'aggregate_output_tps', 'Tokens/sec');
  renderChart('perUserChart', runs, 'avg_per_request_tps', 'Tokens/sec');
  renderChart('latencyChart', runs, 'avg_latency_s', 'Seconds');
  renderChart('ttftChart', runs, 'avg_ttft_s', 'Seconds');
  renderChart('successChart', runs, 'success_rate', 'Success %');
  renderTable(runs);
});
</script>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark concurrent users against LM Studio or Ollama.")
    parser.add_argument("--server", choices=["lmstudio", "ollama", "ollama-native"], default="lmstudio", help="lmstudio and ollama use /v1/chat/completions; ollama-native uses /api/generate.")
    parser.add_argument("--base-url", default="http://localhost:1234", help="LM Studio default: http://localhost:1234. Ollama default is usually http://localhost:11434.")
    parser.add_argument("--model", required=True, help="Model name loaded by LM Studio or Ollama, e.g. gemma3:27b or local model id.")
    parser.add_argument("--concurrency", default="1-10", help="User counts to test, e.g. 1-10 or 1,2,5,10.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Generated tokens per request.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--runtime", help="Optional runtime label, e.g. Vulkan llama.cpp, CUDA, ROCm, Metal, CPU.")
    parser.add_argument("--gpu", help="Optional GPU label, e.g. Radeon Pro R9700 32GB.")
    parser.add_argument("--quantization", help="Optional quantization label, e.g. Q4_K_M.")
    parser.add_argument("--context-size", type=int, help="Optional model/server context size used for this run.")
    parser.add_argument("--notes", help="Optional notes stored in the report, e.g. driver version, power limit, server settings.")
    parser.add_argument("--prompts-file", help="Text file separated by lines or '\\n---\\n', or JSON list of strings.")
    parser.add_argument("--out-dir", default=f"benchmark-results-{now_stamp()}")
    parser.add_argument("--cooldown", type=float, default=2.0, help="Seconds to wait between concurrency groups.")
    parser.add_argument("--warmup", type=int, default=1, help="Number of single-user warmup requests to run before measured results.")
    parser.add_argument("--warmup-tokens", type=int, default=64, help="Generated tokens per warmup request.")
    parser.add_argument("--warmup-pause", type=float, default=1.0, help="Seconds to wait after warmup before measured results.")
    parser.add_argument("--no-html", action="store_true", help="Skip HTML chart output.")
    args = parser.parse_args(argv)

    if args.server == "ollama" and args.base_url == "http://localhost:1234":
        args.base_url = "http://localhost:11434"
    if args.server == "ollama-native" and args.base_url == "http://localhost:1234":
        args.base_url = "http://localhost:11434"

    prompts = load_prompts(args.prompts_file)
    concurrencies = parse_concurrency(args.concurrency)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_results: List[RequestResult] = []
    warmup_results: List[RequestResult] = []
    summaries: List[GroupSummary] = []
    print(f"Benchmarking {args.model} on {args.server} at {args.base_url}")
    print(f"Concurrency groups: {concurrencies}")
    print()
    warmup_results = run_warmup(args, prompts)

    for concurrency in concurrencies:
        group_started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for user_id in range(1, concurrency + 1):
                prompt = prompts[(user_id - 1) % len(prompts)]
                futures.append(
                    executor.submit(
                        run_one,
                        args.server,
                        args.base_url,
                        args.model,
                        prompt,
                        concurrency,
                        user_id,
                        args.max_tokens,
                        args.temperature,
                        args.timeout,
                    )
                )
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        wall = time.perf_counter() - group_started
        results.sort(key=lambda r: r.user_id)
        all_results.extend(results)
        summary = summarize_group(concurrency, results, wall)
        summaries.append(summary)
        print(
            f"users={concurrency:>2} success={summary.success}/{summary.requests} "
            f"aggregate_tok_s={fmt(summary.aggregate_output_tps)} avg_user_tok_s={fmt(summary.avg_per_request_tps)} "
            f"avg_latency_s={fmt(summary.avg_latency_s)} avg_ttft_s={fmt(summary.avg_ttft_s)}"
        )
        if summary.errors:
            print(f"  errors: {' | '.join(summary.errors[:2])}")
        if concurrency != concurrencies[-1] and args.cooldown > 0:
            time.sleep(args.cooldown)

    meta = collect_environment_info(args, concurrencies, len(prompts))
    raw = {
        "meta": meta,
        "summaries": [s.__dict__ for s in summaries],
        "requests": [r.__dict__ | {"latency_s": r.latency_s, "output_tokens_per_s": r.output_tokens_per_s} for r in all_results],
        "warmup_requests": [r.__dict__ | {"latency_s": r.latency_s, "output_tokens_per_s": r.output_tokens_per_s} for r in warmup_results],
    }
    (out_dir / "results.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_csv(out_dir / "results.csv", all_results, summaries)
    write_markdown(out_dir / "report.md", meta, summaries)
    if not args.no_html:
        write_html(out_dir / "report.html", meta, summaries)
        write_compare_html(out_dir / "compare.html")

    print()
    print(f"Wrote: {out_dir.resolve()}")
    print(f"- {out_dir / 'report.md'}")
    print(f"- {out_dir / 'results.csv'}")
    print(f"- {out_dir / 'results.json'}")
    print(f"- {out_dir / 'metadata.json'}")
    if not args.no_html:
        print(f"- {out_dir / 'report.html'}")
        print(f"- {out_dir / 'compare.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
