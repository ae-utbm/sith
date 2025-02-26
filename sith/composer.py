import logging
import signal
import subprocess
import sys

import psutil

from sith import settings


def get_pid() -> int | None:
    """Read the PID file to get the currently running composer if it exists"""
    if not settings.COMPOSER_PID_PATH.exists():
        return None
    with open(settings.COMPOSER_PID_PATH, "r", encoding="utf8") as f:
        return int(f.read())


def write_pid(pid: int):
    """Write currently running composer pid in PID file"""
    if not settings.COMPOSER_PID_PATH.exists():
        settings.COMPOSER_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.COMPOSER_PID_PATH, "w", encoding="utf8") as f:
        _ = f.write(str(pid))


def delete_pid():
    """Delete PID file for cleanup"""
    settings.COMPOSER_PID_PATH.unlink(missing_ok=True)


def is_composer_running() -> bool:
    """Check if the process in the PID file is running"""
    pid = get_pid()
    if pid is None:
        return False
    try:
        return psutil.Process(pid).is_running()
    except psutil.NoSuchProcess:
        return False


def start_composer(procfile: str):
    """Starts the composer and stores the PID as an environment variable
    This allows for running smoothly with the django reloader
    """
    if is_composer_running():
        logging.info(f"Composer is already running with pid {get_pid()}")
        logging.info(
            f"If this is a mistake, please delete {settings.COMPOSER_PID_PATH} and restart the process"
        )
        return
    process = subprocess.Popen(
        [sys.executable, "-m", "honcho", "-f", procfile, "start"],
    )
    write_pid(process.pid)


def stop_composer():
    """Stops the composer if it was started before"""
    if is_composer_running():
        process = psutil.Process(get_pid())
        if process.parent() != psutil.Process():
            logging.info("Currently running composer is controlled by another process")
            return
        process.send_signal(signal.SIGTERM)
        _ = process.wait()
        delete_pid()
