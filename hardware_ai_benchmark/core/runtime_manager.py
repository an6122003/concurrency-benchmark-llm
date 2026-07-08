"""Manage a built-in llama.cpp runtime so users need no LM Studio/Ollama.

``llama-server`` speaks the same OpenAI-compatible streaming API the engine
already targets (server mode "lmstudio"), so the benchmark engine is untouched:
we start the server on a free localhost port, point the engine at it, and stop
it afterwards.

Resolution order for the binary: bundled with the packaged app → previously
downloaded into the app data dir → on PATH. Downloading fetches the official
llama.cpp GitHub release for this OS/arch (small: ~10–30 MB).
"""

from __future__ import annotations

import ctypes.util
import json
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, List, Optional

from .paths import repo_root, runtime_dir

# Fallback when the GitHub API is unreachable; assets verified to exist.
PINNED_TAG = "b9916"
RELEASE_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
DOWNLOAD_URL = "https://github.com/ggml-org/llama.cpp/releases/download/{tag}/{asset}"

SERVER_NAME = "llama-server.exe" if sys.platform == "win32" else "llama-server"
_CHUNK = 1 << 18


def _has_vulkan() -> bool:
    return ctypes.util.find_library("vulkan") is not None or (
        sys.platform == "win32" and ctypes.util.find_library("vulkan-1") is not None)


def asset_name(tag: str, os_name: str = sys.platform,
               arch: str = platform.machine().lower(),
               vulkan: Optional[bool] = None) -> str:
    """Pick the llama.cpp release asset for a platform.

    macOS builds include Metal. On Windows/Linux we prefer the Vulkan build
    (works on NVIDIA/AMD/Intel GPUs with stock drivers, no CUDA download)
    and fall back to CPU when no Vulkan loader is present.
    """
    arm = arch in ("arm64", "aarch64")
    if vulkan is None:
        vulkan = _has_vulkan()
    if os_name == "darwin":
        suffix = "macos-arm64.tar.gz" if arm else "macos-x64.tar.gz"
    elif os_name == "win32":
        if arm:
            suffix = "win-cpu-arm64.zip"
        else:
            suffix = "win-vulkan-x64.zip" if vulkan else "win-cpu-x64.zip"
    else:
        if arm:
            suffix = "ubuntu-vulkan-arm64.tar.gz" if vulkan else "ubuntu-arm64.tar.gz"
        else:
            suffix = "ubuntu-vulkan-x64.tar.gz" if vulkan else "ubuntu-x64.tar.gz"
    return f"llama-{tag}-bin-{suffix}"


def latest_tag(timeout: float = 8.0) -> str:
    try:
        with urllib.request.urlopen(RELEASE_API, timeout=timeout) as response:
            return json.load(response).get("tag_name") or PINNED_TAG
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return PINNED_TAG


def find_server_binary() -> Optional[Path]:
    """Bundled → managed download → PATH; None when nothing is installed."""
    bundled = repo_root() / "runtime" / SERVER_NAME
    if bundled.exists():
        return bundled
    for candidate in sorted(runtime_dir().rglob(SERVER_NAME), reverse=True):
        if candidate.is_file():
            return candidate
    which = shutil.which("llama-server")
    return Path(which) if which else None


def is_installed() -> bool:
    return find_server_binary() is not None


def installed_description() -> str:
    binary = find_server_binary()
    if binary is None:
        return "not installed"
    try:
        tag = binary.parent.relative_to(runtime_dir()).parts[0]
        return f"llama.cpp {tag}"
    except (ValueError, IndexError):
        return f"llama.cpp at {binary.name}"


def install_runtime(on_progress: Callable[[int, int], None] = lambda done, total: None,
                    cancel: Optional[threading.Event] = None) -> Path:
    """Download and unpack llama-server for this machine; returns the binary."""
    tag = latest_tag()
    asset = asset_name(tag)
    dest = runtime_dir() / tag
    archive = runtime_dir() / asset

    request = urllib.request.Request(DOWNLOAD_URL.format(tag=tag, asset=asset))
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.URLError as exc:
        raise OSError(f"Could not download the runtime: {exc.reason}") from exc
    with response, open(archive, "wb") as sink:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while True:
            if cancel is not None and cancel.is_set():
                archive.unlink(missing_ok=True)
                raise OSError("Runtime download cancelled.")
            chunk = response.read(_CHUNK)
            if not chunk:
                break
            sink.write(chunk)
            done += len(chunk)
            on_progress(done, total)

    dest.mkdir(parents=True, exist_ok=True)
    if asset.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(dest)
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(dest)
    archive.unlink(missing_ok=True)

    binary = next((p for p in dest.rglob(SERVER_NAME) if p.is_file()), None)
    if binary is None:
        raise OSError(f"Runtime archive did not contain {SERVER_NAME}.")
    if sys.platform != "win32":
        for tool in binary.parent.iterdir():
            tool.chmod(0o755)
    if sys.platform == "darwin":  # best-effort: clear quarantine on the tools
        subprocess.run(["xattr", "-dr", "com.apple.quarantine", str(dest)],
                       capture_output=True, check=False)
    return binary


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class ManagedServer:
    """A llama-server child process serving one GGUF model for one benchmark."""

    def __init__(self, model_path: Path, context_per_slot: int = 4096,
                 parallel: int = 4, load_timeout_s: float = 300.0):
        self.model_path = Path(model_path)
        self.context_per_slot = context_per_slot
        self.parallel = max(1, min(parallel, 8))
        self.load_timeout_s = load_timeout_s
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._process: Optional[subprocess.Popen] = None
        self._pump: Optional[threading.Thread] = None

    def command(self, binary: Path) -> List[str]:
        return [
            str(binary),
            "-m", str(self.model_path),
            "--host", "127.0.0.1",
            "--port", str(self.port),
            # One context slot per simulated user; beyond that requests queue,
            # which is exactly how a real single-node server behaves.
            "--parallel", str(self.parallel),
            "--ctx-size", str(self.context_per_slot * self.parallel),
            "-ngl", "99",          # offload everything the backend supports
            "--no-webui",
        ]

    def start(self, on_line: Callable[[str], None] = lambda line: None) -> None:
        binary = find_server_binary()
        if binary is None:
            raise OSError("Built-in runtime is not installed yet.")
        if not self.model_path.exists():
            raise OSError(f"Model file not found: {self.model_path.name}")

        self._process = subprocess.Popen(
            self.command(binary), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
            cwd=str(binary.parent))

        def _pump_output():
            for raw in self._process.stdout:
                on_line("[runtime] " + raw.rstrip("\n"))
        self._pump = threading.Thread(target=_pump_output, daemon=True)
        self._pump.start()

        deadline = time.time() + self.load_timeout_s
        while time.time() < deadline:
            if self._process.poll() is not None:
                raise OSError(
                    f"Built-in runtime exited during startup (code {self._process.returncode}). "
                    "The model may be too large for this machine.")
            try:
                with urllib.request.urlopen(self.base_url + "/health", timeout=2) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError, OSError):
                pass
            time.sleep(0.5)
        self.stop()
        raise OSError(f"Built-in runtime did not become ready within {int(self.load_timeout_s)}s.")

    def stop(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
