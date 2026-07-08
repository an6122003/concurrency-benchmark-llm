"""PyInstaller entry point (frozen builds).

multiprocessing.freeze_support() must run before anything else so the
`--engine` child processes work on Windows.
"""

import multiprocessing
import sys

multiprocessing.freeze_support()

from hardware_ai_benchmark.__main__ import main

sys.exit(main())
