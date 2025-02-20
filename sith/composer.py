import os
import signal
import subprocess
import sys

import psutil

COMPOSER_PID = "COMPOSER_PID"


def start_composer(procfile: str):
    """Starts the composer and stores the PID as an environment variable
    This allows for running smoothly with the django reloader
    """
    process = subprocess.Popen(
        [sys.executable, "-m", "honcho", "-f", procfile, "start"],
    )
    os.environ[COMPOSER_PID] = str(process.pid)


def stop_composer():
    """Stops the composer if it was started before"""
    if (pid := os.environ.get(COMPOSER_PID, None)) is not None:
        process = psutil.Process(int(pid))
        process.send_signal(signal.SIGTERM)
        process.wait()
