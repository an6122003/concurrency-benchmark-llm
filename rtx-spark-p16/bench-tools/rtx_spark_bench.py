"""Benchmark orchestrator for the RTX Spark laptop (ASUS ProArt P16, 128 GB).

For each model in models.json it runs these phases:
  bench    llama-bench: classic pp512/tg128, plus the sweep used by ggml-org's
           DGX Spark thread (pp2048 / tg32 at context depth 0..32768)
  batched  llama-batched-bench: aggregate decode with 1..32 parallel sequences
  suite    the concurrency-benchmark-llm suite (8 standard scenarios, a 16K-word
           context test and 12..32 user stress) against llama-server
  mtp      the decode-heavy suite scenarios again with MTP speculative decoding

GPU telemetry from nvidia-smi (1 s) and Windows GPU memory counters are
recorded for every phase. Results land in the repo's gitignored
suite-results-rtx-spark-p16-20261025 folder.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LLAMA = HERE / "llamacpp-cuda-b11671"
REPO = Path(r"C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm")
OUT = REPO / "suite-results-rtx-spark-p16-20261025"
PORT = 8099
BASE_URL = f"http://127.0.0.1:{PORT}"
GPU_LABEL = "NVIDIA RTX Spark N1X (Blackwell, 6144 CUDA cores), 128 GB LPDDR5X unified, ASUS ProArt P16"
RUNTIME_LABEL = "llama.cpp b11671 (CUDA 13, Windows on Arm) llama-server"

SUITE_EXTRA = [
    {"name": "09_context_16k", "description": "Approximate 16K-word (~21K token) long-prompt prefill test.",
     "prompt_set": "context", "approx_prompt_words": 16000, "concurrency": "1", "max_tokens": 160,
     "warmup": 1, "warmup_tokens": 64},
    {"name": "10_team_stress", "description": "Team serving beyond 10 users.",
     "prompt_set": "short_chat", "concurrency": "12,16,24,32", "max_tokens": 300,
     "warmup": 1, "warmup_tokens": 64},
]


class SystemPowerStatus(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]


def power_status() -> dict:
    status = SystemPowerStatus()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
    return {"ac": status.ACLineStatus == 1, "battery_pct": status.BatteryLifePercent}


def battery_mwh() -> int | None:
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-CimInstance -Namespace root\\wmi -ClassName BatteryStatus).RemainingCapacity"],
                             capture_output=True, text=True, timeout=30).stdout.split()
        return int(out[0])
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def idle_charge_watts(seconds: float = 60) -> float | None:
    """Net power flowing into the battery while nothing else runs (negative: draining)."""
    start, t0 = battery_mwh(), time.time()
    time.sleep(seconds)
    end = battery_mwh()
    if start is None or end is None:
        return None
    return (end - start) / ((time.time() - t0) / 3600) / 1000


def wait_for_ac(allow_battery: bool, check_charger: bool = False) -> dict:
    """Block until the laptop runs on a charger that can carry the benchmark.

    A 65 W charger reports "AC online" yet the battery still drains ~60 W
    under load, so every phase waits while the battery is below 30% and
    resumes at 50%. With check_charger, the run also waits until the battery
    gains >= 20 W at idle (or is already full).
    """
    status = power_status()
    if allow_battery:
        return status
    if not status["ac"]:
        log("waiting for AC power (plug in the charger) ...")
        while not status["ac"]:
            time.sleep(15)
            status = power_status()
        log("AC power connected")
        time.sleep(20)  # let the power mode settle
    if status["battery_pct"] < 30:
        log(f"battery at {status['battery_pct']}%, pausing until the charger brings it back to 50% ...")
        while power_status()["battery_pct"] < 50:
            time.sleep(60)
        log("battery back at 50%, resuming")
    while check_charger and power_status()["battery_pct"] < 97:
        watts = idle_charge_watts()
        if watts is None or watts >= 20:
            log(f"charger ok (battery gains {watts if watts is None else round(watts, 1)} W at idle)")
            break
        log(f"charger too weak: battery gains only {watts:.1f} W at idle; plug in the original ASUS adapter")
    return power_status()


def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_models() -> dict:
    # utf-8-sig: PowerShell 5.1 writes a BOM when it edits the file
    return json.loads((HERE / "models.json").read_text(encoding="utf-8-sig"))


def record(entry: dict) -> None:
    manifest = OUT / "manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


class Telemetry:
    """nvidia-smi samples plus Windows GPU dedicated/shared memory counters."""

    def __init__(self, prefix: Path):
        self.prefix = prefix
        self.procs = []

    def __enter__(self):
        smi = open(f"{self.prefix}-gpu.csv", "w", encoding="utf-8")
        smi.write("timestamp,power_w,temp_c,clock_gr_mhz,clock_mem_mhz,mem_used_mib,util_pct,pstate\n")
        smi.flush()
        self.procs.append((subprocess.Popen(
            ["nvidia-smi", "-i", "0", "--query-gpu=timestamp,power.draw,temperature.gpu,clocks.gr,clocks.mem,memory.used,utilization.gpu,pstate",
             "--format=csv,noheader,nounits", "-lms", "1000"], stdout=smi, stderr=subprocess.DEVNULL), smi))
        mem = open(f"{self.prefix}-gpumem.csv", "w", encoding="utf-8")
        self.procs.append((subprocess.Popen(
            ["typeperf", r"\GPU Adapter Memory(*)\Dedicated Usage", r"\GPU Adapter Memory(*)\Shared Usage",
             r"\Memory\Available MBytes", "-si", "2"], stdout=mem, stderr=subprocess.DEVNULL), mem))
        return self

    def __exit__(self, *exc):
        for proc, handle in self.procs:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            handle.close()


def run_logged(cmd: list, log_path: Path, stdout_path: Path | None = None, timeout: float | None = None) -> int:
    log("$ " + " ".join(str(c) for c in cmd))
    with open(log_path, "w", encoding="utf-8") as err:
        out = open(stdout_path, "w", encoding="utf-8") if stdout_path else err
        try:
            proc = subprocess.run([str(c) for c in cmd], stdout=out, stderr=err, cwd=str(LLAMA), timeout=timeout)
        finally:
            if stdout_path:
                out.close()
    return proc.returncode


def load_mode_args(model: dict, flag: str = "--load-mode") -> list:
    """Load mode plus any per-model extra arguments (e.g. a tensor placement override)."""
    args = [flag, model["load_mode"]] if model.get("load_mode") else []
    return args + model.get("extra_args", [])


def phase_bench(key: str, model: dict, out: Path) -> None:
    exe = LLAMA / "llama-bench.exe"
    common = [exe, "-m", model["path"], "-ngl", "999", "-fa", "1", "-ub", "2048", "-o", "json", "--progress"]
    common += load_mode_args(model, "-lm")
    with Telemetry(out / "telemetry-bench"):
        rc1 = run_logged(common + ["-p", "512", "-n", "128", "-r", "5"],
                         out / "bench-classic.log", out / "bench-classic.json")
        rc2 = run_logged(common + ["-p", "2048", "-n", "32", "-d", "0,4096,8192,16384,32768", "-r", "3"],
                         out / "bench-sweep.log", out / "bench-sweep.json")
    log(f"llama-bench done rc={rc1},{rc2}")
    if rc1 or rc2:
        raise RuntimeError(f"llama-bench exited with {rc1},{rc2}")


def phase_quick(key: str, model: dict, out: Path) -> None:
    """pp512/tg128 only: the A/B between GPU memory settings (50 GB vs 96 GB)."""
    exe = LLAMA / "llama-bench.exe"
    cmd = [exe, "-m", model["path"], "-ngl", "999", "-fa", "1", "-ub", "2048", "-o", "json",
           "-p", "512", "-n", "128", "-r", "5"] + load_mode_args(model, "-lm")
    with Telemetry(out / "telemetry-quick"):
        rc = run_logged(cmd, out / "bench-quick.log", out / "bench-quick.json")
    log(f"quick llama-bench done rc={rc}")
    if rc:
        raise RuntimeError(f"llama-bench exited with {rc}")


def phase_batched(key: str, model: dict, out: Path) -> None:
    exe = LLAMA / "llama-batched-bench.exe"
    cmd = [exe, "-m", model["path"], "-ngl", "999", "-fa", "on", "-c", "32768", "-b", "2048", "-ub", "2048",
           "-npp", "512", "-ntg", "128", "-npl", "1,2,4,8,16,32", "-kvu", "--output-format", "jsonl"]
    cmd += load_mode_args(model)
    with Telemetry(out / "telemetry-batched"):
        rc = run_logged(cmd, out / "batched.log", out / "batched.jsonl")
    log(f"batched-bench done rc={rc}")
    if rc:
        raise RuntimeError(f"llama-batched-bench exited with {rc}")


def phase_ref(key: str, model: dict, out: Path) -> None:
    """llama-batched-bench with the exact parameters of the official DGX Spark table."""
    exe = LLAMA / "llama-batched-bench.exe"
    cmd = [exe, "-m", model["path"], "-ngl", "999", "-fa", "on", "-c", "140000", "-b", "2048", "-ub", "2048",
           "-npp", "512,4096", "-ntg", "32", "-npl", "1,2,4,8,16,32", "-kvu", "--output-format", "jsonl"]
    with Telemetry(out / "telemetry-ref"):
        rc = run_logged(cmd, out / "batched-ref.log", out / "batched-ref.jsonl")
    log(f"reference batched-bench done rc={rc}")
    if rc:
        raise RuntimeError(f"llama-batched-bench exited with {rc}")


def server_cmd(key: str, model: dict, mtp: bool) -> list:
    cmd = [LLAMA / "llama-server.exe", "-m", model["path"], "--host", "127.0.0.1", "--port", str(PORT),
           "--alias", key, "-ngl", "999", "--fit", "off", "-fa", "on",
           "-c", str(model.get("ctx", 65536)), "-np", str(model.get("np", 32)), "--kv-unified",
           "-b", "2048", "-ub", "2048", "--no-cache-prompt", "--cache-ram", "0",
           "--jinja", "--no-webui", "--metrics"]
    cmd += model.get("reasoning_args", [])
    cmd += load_mode_args(model)
    if mtp:
        cmd += model["mtp"]["spec"]
    return [str(c) for c in cmd]


class Server:
    def __init__(self, cmd: list, log_path: Path):
        self.cmd = cmd
        self.log_path = log_path
        self.proc = None

    def __enter__(self):
        log("$ " + " ".join(self.cmd))
        self.handle = open(self.log_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(self.cmd, stdout=self.handle, stderr=subprocess.STDOUT, cwd=str(LLAMA))
        t0 = time.time()
        while time.time() - t0 < 1200:
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server exited with {self.proc.returncode}, see {self.log_path}")
            try:
                with urllib.request.urlopen(BASE_URL + "/health", timeout=3) as resp:
                    if resp.status == 200:
                        self.load_s = time.time() - t0
                        log(f"server ready in {self.load_s:.0f} s")
                        return self
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(1)
        raise RuntimeError("llama-server did not become ready")

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.handle.close()
        time.sleep(5)  # let the driver release memory


def save_props(out: Path, tag: str) -> None:
    for path in ("/props", "/v1/models"):
        try:
            with urllib.request.urlopen(BASE_URL + path, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict):
                data.pop("chat_template", None)
            name = path.strip("/").replace("/", "-")
            (out / f"{tag}-{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - diagnostics only
            log(f"could not save {path}: {exc}")


def run_suite(key: str, model: dict, out_dir: Path, scenarios: list, tag: str, notes: str) -> None:
    config = {
        "suite_name": f"rtx-spark-p16-{key}-{tag}",
        "targets": [{
            "name": key,
            "server": "lmstudio",
            "base_url": BASE_URL,
            "model": key,
            "runtime": RUNTIME_LABEL,
            "gpu": GPU_LABEL,
            "quantization": model["quant"],
            "context_size": model.get("ctx", 65536),
            "notes": notes,
        }],
        "scenarios": scenarios,
    }
    cfg_path = out_dir.parent / f"suite-config-{tag}.json"
    cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    cmd = [sys.executable, str(REPO / "benchmark_suite.py"), "--config", str(cfg_path), "--out-dir", str(out_dir),
           "--python", sys.executable]
    log("$ " + " ".join(cmd))
    with open(out_dir.parent / f"suite-{tag}.log", "w", encoding="utf-8") as handle:
        subprocess.run(cmd, cwd=str(REPO), stdout=handle, stderr=subprocess.STDOUT, check=False)


def standard_scenarios() -> list:
    return json.loads((REPO / "suite-config.example.json").read_text(encoding="utf-8"))["scenarios"]


def phase_suite(key: str, model: dict, out: Path) -> None:
    scenarios = standard_scenarios() + [dict(s) for s in SUITE_EXTRA]
    if model.get("np", 32) < 32:
        for s in scenarios:
            if s["name"] == "10_team_stress":
                s["concurrency"] = "12,16"
    cmd = server_cmd(key, model, mtp=False)
    (out / "server-args-suite.json").write_text(json.dumps(cmd, indent=2), encoding="utf-8")
    notes = "server: " + " ".join(cmd[3:])
    with Telemetry(out / "telemetry-suite"), Server(cmd, out / "server-suite.log") as server:
        save_props(out, "suite")
        run_suite(key, model, out / "suite", scenarios, "suite", notes)
        record({"model": key, "phase": "suite-load", "load_s": server.load_s})


def phase_team(key: str, model: dict, out: Path) -> None:
    """Only the concurrency curve (team chat 1-10 users + 12-32 user stress), for secondary models."""
    scenarios = [s for s in standard_scenarios() if s["name"] == "02_team_concurrency"]
    scenarios += [dict(s) for s in SUITE_EXTRA if s["name"] == "10_team_stress"]
    cmd = server_cmd(key, model, mtp=False)
    (out / "server-args-suite.json").write_text(json.dumps(cmd, indent=2), encoding="utf-8")
    notes = "server: " + " ".join(cmd[3:])
    with Telemetry(out / "telemetry-suite"), Server(cmd, out / "server-suite.log") as server:
        save_props(out, "suite")
        run_suite(key, model, out / "suite", scenarios, "suite", notes)
        record({"model": key, "phase": "team-load", "load_s": server.load_s})


def phase_mtp(key: str, model: dict, out: Path) -> None:
    if not model.get("mtp"):
        log(f"{key}: no MTP config, skipping")
        return
    wanted = {"02_team_concurrency": "1,2,4,8", "03_peak_decode_long_output": None, "06_coding_smoke": None}
    scenarios = []
    for s in standard_scenarios():
        if s["name"] in wanted:
            s = dict(s)
            if wanted[s["name"]]:
                s["concurrency"] = wanted[s["name"]]
            scenarios.append(s)
    cmd = server_cmd(key, model, mtp=True)
    (out / "server-args-mtp.json").write_text(json.dumps(cmd, indent=2), encoding="utf-8")
    notes = "MTP speculative decoding. server: " + " ".join(cmd[3:])
    with Telemetry(out / "telemetry-mtp"), Server(cmd, out / "server-mtp.log") as server:
        save_props(out, "mtp")
        run_suite(key, model, out / "suite-mtp", scenarios, "mtp", notes)
        record({"model": key, "phase": "mtp-load", "load_s": server.load_s})


PHASES = {"bench": phase_bench, "quick": phase_quick, "batched": phase_batched, "suite": phase_suite,
          "team": phase_team, "mtp": phase_mtp, "ref": phase_ref}
HOLD = HERE / "HOLD"  # while this file exists, no new GPU job starts


def wait_for_hold() -> None:
    if HOLD.exists():
        log(f"on hold ({HOLD.name} file present) ...")
        while HOLD.exists():
            time.sleep(10)
        log("hold released")


def done_phases(tag: str) -> set:
    manifest = OUT / "manifest.jsonl"
    if not manifest.exists():
        return set()
    done = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("status") == "ok" and e.get("tag", "") == tag and e.get("phase") in PHASES:
            done.add((e["model"], e["phase"]))
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("models", nargs="*", help="model keys from models.json")
    parser.add_argument("--phases", default="bench,batched,suite,mtp")
    parser.add_argument("--allow-battery", action="store_true", help="run even when the laptop is unplugged")
    parser.add_argument("--tag", default="", help="suffix for the per-model output folder (e.g. battery)")
    parser.add_argument("--wait-power", action="store_true", help="only wait until power allows the next GPU job")
    parser.add_argument("--check-charger", action="store_true", help="also require a charger that carries the load")
    parser.add_argument("--skip-done", action="store_true", help="skip phases the manifest already records as ok")
    args = parser.parse_args()

    models = load_models()
    OUT.mkdir(parents=True, exist_ok=True)
    wait_for_hold()
    wait_for_ac(args.allow_battery, check_charger=args.check_charger)
    if args.wait_power:
        return 0
    done = done_phases(args.tag) if args.skip_done else set()
    for key in args.models:
        model = models[key]
        if not Path(model["path"]).exists():
            log(f"{key}: model file missing, skipping ({model['path']})")
            continue
        out = OUT / (key + (f"-{args.tag}" if args.tag else ""))
        out.mkdir(parents=True, exist_ok=True)
        for phase in args.phases.split(","):
            if (key, phase) in done:
                log(f"{key} / {phase}: already done, skipping")
                continue
            wait_for_hold()
            power = wait_for_ac(args.allow_battery)
            log(f"=== {key} / {phase} (AC={power['ac']}, battery={power['battery_pct']}%) ===")
            t0 = time.time()
            status = "ok"
            try:
                PHASES[phase](key, model, out)
            except Exception as exc:  # noqa: BLE001 - keep going with the next phase/model
                status = f"error: {exc}"
                log(f"{key} / {phase} failed: {exc}")
            power_end = power_status()
            record({"model": key, "phase": phase, "tag": args.tag, "status": status,
                    "started": dt.datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
                    "duration_s": round(time.time() - t0, 1), "power_start": power, "power_end": power_end,
                    "battery_assisted": power_end["battery_pct"] <= power["battery_pct"] - 2})
            log(f"=== {key} / {phase} finished in {time.time() - t0:.0f} s ({status}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
