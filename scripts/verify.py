"""Local verification driver. Run from the project venv; stops at the first failed check."""

import argparse
import subprocess
import sys
from pathlib import Path


def run(*args: str) -> None:
    print("+", sys.executable, *args, flush=True)
    subprocess.run([sys.executable, *args], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.fix:
        run("scripts/generate_reference.py")
        run("-m", "ruff", "check", ".", "--fix")
        run("-m", "ruff", "format", ".")
    run("-m", "ruff", "check", ".")
    run("-m", "ruff", "format", "--check", ".")
    run("-m", "mypy")
    run("scripts/generate_reference.py", "--check")
    run("-m", "pytest", "-p", "no:cacheprovider", "--cov=ta_config", "--cov-report=term-missing")
    if args.release:
        constraints = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze", "--exclude-editable"], text=True
        )
        (root / "constraints-dev.txt").write_text(
            "# Tested contributor environment; Python 3.12 on Windows.\n" + constraints,
            encoding="utf-8",
        )
        run("-m", "build")
        run("scripts/wheel_smoke.py", "dist/ta_config-0.2.0-py3-none-any.whl")
        run("-m", "pip_audit")
        run("scripts/benchmark.py")


if __name__ == "__main__":
    main()
