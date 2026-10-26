"""Split the working-tree diff into topic commits by hunk, staging each with `git apply --cached`.

    python split_commits.py <repo> <author name> <author email>
"""
import re
import subprocess
import sys

REPO, NAME, EMAIL = sys.argv[1], sys.argv[2], sys.argv[3]

COMMITS = [
    ("uv", lambda h: "UV_PYTHON_INSTALL_DIR" in h,
     "Windows setup: keep uv's Pythons in the workshop folder\n\n"
     "The first install on a real RTX Spark stopped at the Python step: uv\n"
     "venv failed with \"Missing expected target directory for Python minor\n"
     "version link\". From a packaged (MSIX) terminal, writes to %APPDATA%\n"
     "land in the package's own folder, and the junction uv makes from 3.13\n"
     "to 3.13.x points at the real %APPDATA%, where nothing is. With\n"
     "UV_PYTHON_INSTALL_DIR in .run\\python the Pythons stay inside the\n"
     "workshop folder, which also makes removing the workshop one folder.\n"),
    ("hf", lambda h: "max_workers=1" in h,
     "Windows setup: download Hugging Face models one file at a time\n\n"
     "Without the right to make symlinks (no Developer Mode, not an\n"
     "administrator: a normal demo PC), huggingface_hub marks a cache folder\n"
     "as supporting symlinks before it tests it, so its parallel download\n"
     "workers race the test and crash with WinError 1314. That stopped\n"
     "Hands-on 1's base model on the RTX Spark (GitHub's runners are\n"
     "administrators, so CI never saw it). One worker removes the race; the\n"
     "single large file of each model dominates the time anyway.\n"),
    ("awake", lambda h: "Set-KeepAwake" in h or "Test-OnBattery" in h,
     "Windows setup: keep the laptop awake while it installs, warn on battery\n\n"
     "The RTX Spark machines are laptops and the install runs for up to an\n"
     "hour with nobody touching them: idle sleep would cut the downloads off.\n"
     "SetThreadExecutionState holds the PC and its screen on until setup\n"
     "exits (nothing is changed for good), and the computer check warns\n"
     "when the charger is not plugged in.\n"),
    ("one-command", lambda h: True,
     "Windows edition: one command from the windows branch, measured on an RTX Spark\n\n"
     "install.ps1 now installs the windows branch by default, so a demo PC\n"
     "needs only `irm .../windows/install.ps1 | iex` (main has no Windows\n"
     "edition yet). The operator guide and README give that command and\n"
     "what a real RTX Spark measured: a 38-minute first install, about 58 GB\n"
     "downloaded, and how long each lab and batch takes on stage.\n"),
]


def git(*args, inp=None):
    p = subprocess.run(["git", "-C", REPO, *args], input=inp, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{p.stderr.decode('utf-8', 'replace')}")
    return p.stdout


def hunks_by_file(diff: bytes):
    """[(file header, [hunk, ...]), ...] from a unified diff."""
    files = []
    for chunk in re.split(rb"(?m)^(?=diff --git )", diff):
        if not chunk.strip():
            continue
        parts = re.split(rb"(?m)^(?=@@ )", chunk)
        files.append((parts[0], parts[1:]))
    return files


for key, wants, message in COMMITS:
    diff = git("diff", "--no-color", "-U3")
    if not diff.strip():
        break
    patch = b""
    for head, hunks in hunks_by_file(diff):
        mine = [h for h in hunks if wants(h.decode("utf-8", "replace"))]
        if mine:
            patch += head + b"".join(mine)
    if not patch:
        print(f"{key}: nothing to commit")
        continue
    git("apply", "--cached", "--recount", "-", inp=patch)
    git("-c", f"user.name={NAME}", "-c", f"user.email={EMAIL}", "commit", "-q", "-m", message)
    print(f"{key}: committed " + git("log", "-1", "--format=%h %s").decode("utf-8").strip())

left = git("diff", "--stat").decode("utf-8").strip()
print("left uncommitted:", left or "nothing")
