"""Entry point: `python -m hardware_ai_benchmark`.

Special mode: `--engine <args...>` runs the benchmark engine in-process.
The GUI uses this to spawn benchmark child processes from a frozen build,
where no separate Python interpreter exists.
"""

import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--engine":
        from hardware_ai_benchmark.core.engine import run_engine_worker
        return run_engine_worker(sys.argv[2:])
    from hardware_ai_benchmark.app.main import run
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
