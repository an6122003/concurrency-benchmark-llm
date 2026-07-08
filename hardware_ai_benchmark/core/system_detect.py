"""Cross-platform system detection.

Reuses the engine's battle-tested collectors (nvidia-smi, rocm-smi,
system_profiler, Windows registry, lspci) and adds: platform/arch fields,
AI backend availability probes, and graceful per-adapter failure handling.
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
import urllib.request
from typing import Any, Dict, List

from . import engine


def _safe(collector, fallback):
    try:
        return collector()
    except Exception as exc:  # detection must never crash the app
        return {**fallback, "error": str(exc)}


def detect_platform() -> Dict[str, str]:
    return {
        "os": platform.system(),                  # Windows | Darwin | Linux
        "os_pretty": {"Darwin": "macOS"}.get(platform.system(), platform.system()),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "arch": platform.machine(),               # x86_64 | arm64 | aarch64 | AMD64
        "python": sys.version.split()[0],
    }


def _http_ok(url: str, timeout: float = 0.8) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout):
            return True
    except Exception:
        return False


def detect_backends() -> List[Dict[str, Any]]:
    """Which AI runtimes/backends look available on this machine."""
    backends: List[Dict[str, Any]] = []
    system = platform.system()

    backends.append({"name": "CUDA", "available": shutil.which("nvidia-smi") is not None,
                     "hint": "NVIDIA driver tools detected" if shutil.which("nvidia-smi") else "nvidia-smi not found"})
    backends.append({"name": "ROCm", "available": shutil.which("rocm-smi") is not None,
                     "hint": "AMD ROCm tools detected" if shutil.which("rocm-smi") else "rocm-smi not found"})
    if system == "Darwin":
        backends.append({"name": "Metal", "available": True, "hint": "Built into macOS"})
    if system in ("Windows", "Linux"):
        backends.append({"name": "Vulkan", "available": shutil.which("vulkaninfo") is not None or system == "Windows",
                         "hint": "Common on Windows/Linux GPU drivers"})

    lmstudio = _http_ok("http://localhost:1234/v1/models")
    ollama = _http_ok("http://localhost:11434/api/tags")
    backends.append({"name": "LM Studio server", "available": lmstudio,
                     "hint": "Responding on localhost:1234" if lmstudio else "Not responding on localhost:1234"})
    backends.append({"name": "Ollama server", "available": ollama,
                     "hint": "Responding on localhost:11434" if ollama else "Not responding on localhost:11434"})
    return backends


def list_server_models(server: str, base_url: str) -> List[str]:
    """Model ids the local server reports, for the config screen dropdown."""
    try:
        if server == "ollama-native":
            url = f"{base_url.rstrip('/')}/api/tags"
            with urllib.request.urlopen(url, timeout=2) as response:
                payload = json.load(response)
            return [m.get("name", "") for m in payload.get("models", []) if m.get("name")]
        url = f"{base_url.rstrip('/')}/v1/models"
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.load(response)
        return [m.get("id", "") for m in payload.get("data", []) if m.get("id")]
    except Exception:
        return []


def detect_all(extended: bool = True) -> Dict[str, Any]:
    """Full system snapshot shown on the Setup screen and stored in results."""
    try:
        eng = engine.load_engine()
        cpu = _safe(eng.collect_cpu_info, {"processor": platform.processor() or "Unknown"})
        memory = _safe(eng.collect_memory_info, {"total_human": "unknown"})
        gpu = _safe(eng.collect_gpu_info, {"detected": []}) if extended else {"detected": []}
    except Exception as exc:
        cpu = {"processor": platform.processor() or "Unknown", "error": str(exc)}
        memory = {"total_human": "unknown"}
        gpu = {"detected": []}

    return {
        "platform": detect_platform(),
        "cpu": cpu,
        "memory": memory,
        "gpu": gpu,
        "backends": detect_backends(),
    }


def summarize_for_display(info: Dict[str, Any]) -> List[tuple]:
    """(label, value) pairs for the Setup screen."""
    plat = info.get("platform", {})
    cpu = info.get("cpu", {})
    memory = info.get("memory", {})
    gpus = (info.get("gpu") or {}).get("detected") or []
    gpu_names = "; ".join(g.get("name", "?") for g in gpus) or "Not detected"
    vram = "; ".join(f"{g.get('name', '?')}: {g.get('vram_total_human', '?')}"
                     for g in gpus if g.get("vram_total_human")) or "Unknown"
    available = [b["name"] for b in info.get("backends", []) if b.get("available")]
    return [
        ("Operating system", f"{plat.get('os_pretty', '?')} {plat.get('os_release', '')}".strip()),
        ("Architecture", plat.get("arch", "?")),
        ("CPU", cpu.get("processor") or cpu.get("name") or "Unknown"),
        ("System RAM", memory.get("total_human", "Unknown")),
        ("GPU", gpu_names),
        ("VRAM", vram),
        ("Available backends", ", ".join(available) or "None detected"),
        ("Python", plat.get("python", "?")),
    ]
