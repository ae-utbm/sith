import logging
import signal
import subprocess
import sys
from pathlib import Path

import psutil

from sith import settings


def get_pid_file(procfile: Path) -> Path:
    """Get the PID file associated with a procfile"""
    return settings.BASE_DIR / procfile.with_suffix(f"{procfile.suffix}.pid")


def get_pid(procfile: Path) -> int | None:
    """Read the PID file to get the currently running composer if it exists"""
    file = get_pid_file(procfile)
    if not file.exists():
        return None
    with open(file, "r", encoding="utf8") as f:
        return int(f.read())


def write_pid(procfile: Path, pid: int):
    """Write currently running composer pid in PID file"""
    file = get_pid_file(procfile)
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, "w", encoding="utf8") as f:
        _ = f.write(str(pid))


def delete_pid(procfile: Path):
    """Delete PID file for cleanup"""
    get_pid_file(procfile).unlink(missing_ok=True)


def is_composer_running(procfile: Path) -> bool:
    """Check if the process in the PID file is running"""
    pid = get_pid(procfile)
    if pid is None:
        return False
    try:
        return psutil.Process(pid).is_running()
    except psutil.NoSuchProcess:
        return False


def start_composer(procfile: Path):
    """Starts the composer and stores the PID as an environment variable
    This allows for running smoothly with the django reloader
    """
    if is_composer_running(procfile):
        logging.info(
            f"Composer for {procfile} is already running with pid {get_pid(procfile)}"
        )
        logging.info(
            f"If this is a mistake, please delete {get_pid_file(procfile)} and restart the process"
        )
        return
    process = subprocess.Popen(
        [sys.executable, "-m", "honcho", "-f", str(procfile), "start"],
    )
    write_pid(procfile, process.pid)


def stop_composer(procfile: Path):
    """Stops the composer if it was started before"""
    if is_composer_running(procfile):
        process = psutil.Process(get_pid(procfile))
        if process.parent() != psutil.Process():
            logging.info(
                f"Currently running composer for {procfile} is controlled by another process"
            )
            return
        process.send_signal(signal.SIGTERM)
        _ = process.wait()
        delete_pid(procfile)
