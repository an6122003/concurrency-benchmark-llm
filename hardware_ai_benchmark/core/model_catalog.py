"""Curated GGUF model catalog with one-click downloads for the built-in runtime.

All entries are public, ungated Hugging Face files (verified 2026-07). Sizes
are the real download sizes; ``min_ram_gb`` is a conservative "runs comfortably"
figure (weights + context + OS headroom), used only for UI fit hints.
"""

from __future__ import annotations

import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from .paths import models_dir

_CHUNK = 1 << 18  # 256 KiB


@dataclass(frozen=True)
class CatalogModel:
    key: str
    name: str            # display name, also used as the result's model label
    params: str          # human parameter count, e.g. "4B"
    quantization: str
    size_mb: int         # download size
    min_ram_gb: int
    url: str
    filename: str
    license: str
    blurb: str           # one-line plain-language description


CATALOG: List[CatalogModel] = [
    CatalogModel(
        key="smollm2-135m", name="SmolLM2 135M (tiny sanity check)",
        params="135M", quantization="Q4_K_M", size_mb=101, min_ram_gb=1,
        url="https://huggingface.co/unsloth/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_K_M.gguf",
        filename="SmolLM2-135M-Instruct-Q4_K_M.gguf", license="Apache 2.0",
        blurb="Smallest download. Verifies the pipeline works — not a serious benchmark."),
    CatalogModel(
        key="qwen3-0.6b", name="Qwen3 0.6B", params="0.6B",
        quantization="Q4_K_M", size_mb=378, min_ram_gb=2,
        url="https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf",
        filename="Qwen3-0.6B-Q4_K_M.gguf", license="Apache 2.0",
        blurb="Very small and fast. Good first real test on any machine."),
    CatalogModel(
        key="qwen3-1.7b", name="Qwen3 1.7B", params="1.7B",
        quantization="Q4_K_M", size_mb=1056, min_ram_gb=4,
        url="https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf",
        filename="Qwen3-1.7B-Q4_K_M.gguf", license="Apache 2.0",
        blurb="Small model that still produces meaningful throughput numbers."),
    CatalogModel(
        key="llama-3.2-3b", name="Llama 3.2 3B", params="3B",
        quantization="Q4_K_M", size_mb=1926, min_ram_gb=6,
        url="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf", license="Llama 3.2 Community",
        blurb="Popular mid-small model; a widely comparable reference point."),
    CatalogModel(
        key="qwen3-4b", name="Qwen3 4B", params="4B",
        quantization="Q4_K_M", size_mb=2382, min_ram_gb=8,
        url="https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
        filename="Qwen3-4B-Instruct-2507-Q4_K_M.gguf", license="Apache 2.0",
        blurb="The recommended community benchmark model: fits most machines."),
    CatalogModel(
        key="qwen3-8b", name="Qwen3 8B", params="8B",
        quantization="Q4_K_M", size_mb=4795, min_ram_gb=12,
        url="https://huggingface.co/unsloth/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf",
        filename="Qwen3-8B-Q4_K_M.gguf", license="Apache 2.0",
        blurb="Mid-size test for 16 GB+ machines and dedicated GPUs."),
    CatalogModel(
        key="qwen3-14b", name="Qwen3 14B", params="14B",
        quantization="Q4_K_M", size_mb=8585, min_ram_gb=16,
        url="https://huggingface.co/unsloth/Qwen3-14B-GGUF/resolve/main/Qwen3-14B-Q4_K_M.gguf",
        filename="Qwen3-14B-Q4_K_M.gguf", license="Apache 2.0",
        blurb="Heavy test for high-end GPUs and 32 GB+ machines."),
]


def by_key(key: str) -> Optional[CatalogModel]:
    return next((m for m in CATALOG if m.key == key), None)


def local_path(model: CatalogModel) -> Path:
    return models_dir() / model.filename


def is_downloaded(model: CatalogModel) -> bool:
    path = local_path(model)
    # Guard against truncated files from a previous crash: within 5% of the
    # catalog size counts as complete (HF sizes can drift slightly on re-quant).
    return path.exists() and path.stat().st_size >= model.size_mb * 1024 * 1024 * 0.95


def fit_hint(model: CatalogModel, total_ram_gb: Optional[float]) -> str:
    """Plain-language RAM fit warning for the UI; empty string when it fits."""
    if not total_ram_gb:
        return ""
    if total_ram_gb < model.min_ram_gb:
        return f"needs ~{model.min_ram_gb} GB RAM — likely too big for this machine"
    if total_ram_gb < model.min_ram_gb * 1.5:
        return f"needs ~{model.min_ram_gb} GB RAM — will be tight on this machine"
    return ""


def download(model: CatalogModel,
             on_progress: Callable[[int, int], None] = lambda done, total: None,
             cancel: Optional[threading.Event] = None) -> Path:
    """Download to models_dir with resume support. Raises OSError on failure.

    on_progress(bytes_done, bytes_total); cancel event aborts and keeps the
    .part file so the next attempt resumes.
    """
    target = local_path(model)
    if is_downloaded(model):
        return target
    part = target.with_suffix(target.suffix + ".part")
    done = part.stat().st_size if part.exists() else 0

    request = urllib.request.Request(model.url)
    if done:
        request.add_header("Range", f"bytes={done}-")
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as exc:
        if exc.code == 416:  # .part is already the full file
            part.rename(target)
            return target
        raise OSError(f"Download failed (HTTP {exc.code}) for {model.name}") from exc
    except urllib.error.URLError as exc:
        raise OSError(f"Could not reach huggingface.co: {exc.reason}") from exc

    with response:
        if done and response.status != 206:  # server ignored Range; restart
            done = 0
        total = done + int(response.headers.get("Content-Length") or 0)
        mode = "ab" if done else "wb"
        with open(part, mode) as sink:
            while True:
                if cancel is not None and cancel.is_set():
                    raise OSError("Download cancelled.")
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                sink.write(chunk)
                done += len(chunk)
                on_progress(done, total)
    part.rename(target)
    return target
