"""Convenience runner that starts the Flask API and Streamlit UI together."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent


def _start_backend(env: dict[str, str]) -> subprocess.Popen:
    """Launch the Flask backend as a child process."""
    return subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=PROJECT_ROOT,
        env=env,
    )


def _start_streamlit(env: dict[str, str]) -> subprocess.Popen:
    """Launch the Streamlit frontend."""
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"],
        cwd=PROJECT_ROOT,
        env=env,
    )


def _gracefully_stop(process: subprocess.Popen, timeout: float = 10.0) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> None:
    env = os.environ.copy()
    backend: Optional[subprocess.Popen] = None
    streamlit: Optional[subprocess.Popen] = None

    try:
        print("Starting Flask backend on http://localhost:5000 ...")
        backend = _start_backend(env)
        time.sleep(10)

        print("Starting Streamlit frontend on http://localhost:8501 ...")
        streamlit = _start_streamlit(env)
        print("Both services are running. Press Ctrl+C to stop.")

        streamlit.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if streamlit is not None:
            _gracefully_stop(streamlit)
        if backend is not None:
            _gracefully_stop(backend)


if __name__ == "__main__":
    main()
