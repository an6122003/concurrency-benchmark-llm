"""Benchmark configuration: presets, validation, warnings, CLI arg building."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Dict, List, Optional

from .paths import results_dir


def _parse_concurrency(text: str) -> List[int]:
    """Same grammar as the engine: '1-10' or '1,2,5,10'."""
    values: List[int] = []
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start, _, end = part.partition("-")
            values.extend(range(int(start), int(end) + 1))
        else:
            values.append(int(part))
    return sorted(set(v for v in values if v > 0))


@dataclass
class BenchmarkConfig:
    # Connection
    server: str = "lmstudio"                     # lmstudio | ollama | ollama-native
    base_url: str = "http://localhost:1234"
    model: str = ""

    # Workload
    concurrency: str = "1-8"
    max_tokens: int = 256
    temperature: float = 0.2
    timeout_s: float = 600.0
    warmup: int = 1
    cooldown_s: float = 2.0

    # Optional labels (engine also auto-detects where possible)
    runtime_label: str = ""
    gpu_label: str = ""
    quantization: str = ""
    context_size: Optional[int] = None
    notes: str = ""

    # App-level options (not passed to the engine)
    out_dir: str = ""                            # empty -> auto under results_dir()
    preset: str = "standard"
    preset_hint: str = ""                        # presentation only
    collect_extended_info: bool = True
    include_metadata_in_upload: bool = True
    auto_upload: bool = False
    user_alias: str = ""

    APP_ONLY_FIELDS = ("out_dir", "preset", "preset_hint", "collect_extended_info",
                       "include_metadata_in_upload", "auto_upload", "user_alias")

    # ---------- presets ----------

    @staticmethod
    def presets() -> Dict[str, "BenchmarkConfig"]:
        return {
            "quick": BenchmarkConfig(
                preset="quick", concurrency="1,2,4", max_tokens=128, warmup=1,
                preset_hint="About 3–5 minutes. A fast sanity check."),
            "standard": BenchmarkConfig(
                preset="standard", concurrency="1-8", max_tokens=256, warmup=1,
                preset_hint="About 10–20 minutes. The recommended community test."),
            "full": BenchmarkConfig(
                preset="full", concurrency="1-10", max_tokens=512, warmup=1,
                preset_hint="About 30–60 minutes. Full sweep, longer generations."),
            "stress": BenchmarkConfig(
                preset="stress", concurrency="1-16", max_tokens=1024, warmup=2,
                timeout_s=900.0,
                preset_hint="An hour or more. Pushes queueing and memory limits."),
        }

    # ---------- validation ----------

    def validate(self) -> List[str]:
        """Hard errors that must be fixed before running."""
        errors: List[str] = []
        if not self.model.strip():
            errors.append("Model is required. Pick the model loaded in your server.")
        if self.server not in ("lmstudio", "ollama", "ollama-native"):
            errors.append(f"Unknown server type: {self.server}")
        if not self.base_url.startswith(("http://", "https://")):
            errors.append("Server URL must start with http:// or https://")
        try:
            if not _parse_concurrency(self.concurrency):
                errors.append("Concurrency must contain at least one user count.")
        except ValueError:
            errors.append("Concurrency must look like '1-8' or '1,2,4,8'.")
        if not 1 <= self.max_tokens <= 8192:
            errors.append("Max tokens must be between 1 and 8192.")
        if self.warmup < 0:
            errors.append("Warmup runs cannot be negative.")
        if self.timeout_s <= 0:
            errors.append("Timeout must be positive.")
        return errors

    def warnings(self) -> List[str]:
        """Soft warnings about runtime, stability, and memory."""
        warns: List[str] = []
        try:
            users = _parse_concurrency(self.concurrency)
        except ValueError:
            users = []
        if users and max(users) > 10:
            warns.append(f"Testing up to {max(users)} concurrent users can queue hard or crash smaller servers.")
        if self.max_tokens >= 1024:
            warns.append("1024+ tokens per request makes each stage several times longer.")
        if self.context_size and self.context_size > 32768:
            warns.append("Context above 32K can exhaust VRAM on many GPUs.")
        if users and len(users) * self.max_tokens > 8000:
            warns.append("This combination may take well over an hour.")
        if self.warmup == 0:
            warns.append("Without warmup, the 1-user score includes model load time and looks worse than reality.")
        return warns

    # ---------- conversions ----------

    def concurrency_list(self) -> List[int]:
        return _parse_concurrency(self.concurrency)

    def resolved_out_dir(self) -> Path:
        if self.out_dir:
            return Path(self.out_dir)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        return results_dir() / f"run-{stamp}"

    def to_cli_args(self, out_dir: Path) -> List[str]:
        args = [
            "--server", self.server,
            "--base-url", self.base_url,
            "--model", self.model,
            "--concurrency", self.concurrency,
            "--max-tokens", str(self.max_tokens),
            "--temperature", str(self.temperature),
            "--timeout", str(self.timeout_s),
            "--warmup", str(self.warmup),
            "--cooldown", str(self.cooldown_s),
            "--out-dir", str(out_dir),
        ]
        if self.runtime_label:
            args += ["--runtime", self.runtime_label]
        if self.gpu_label:
            args += ["--gpu", self.gpu_label]
        if self.quantization:
            args += ["--quantization", self.quantization]
        if self.context_size:
            args += ["--context-size", str(self.context_size)]
        if self.notes:
            args += ["--notes", self.notes]
        return args

    def to_dict(self, include_app_fields: bool = True) -> Dict:
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        if not include_app_fields:
            for key in self.APP_ONLY_FIELDS:
                data.pop(key, None)
        return data

    @staticmethod
    def from_dict(data: Dict) -> "BenchmarkConfig":
        known = {f.name for f in fields(BenchmarkConfig)}
        return BenchmarkConfig(**{k: v for k, v in data.items() if k in known})
