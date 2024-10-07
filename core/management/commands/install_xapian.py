#
# Copyright 2024 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

import hashlib
import multiprocessing
import os
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import tomli
import urllib3
from django.core.management.base import BaseCommand, CommandParser, OutputWrapper
from urllib3.response import HTTPException


@dataclass
class XapianSpec:
    version: str
    core_sha1: str
    bindings_sha1: str

    @classmethod
    def from_pyproject(cls) -> Self:
        with open(
            Path(__file__).parent.parent.parent.parent / "pyproject.toml", "rb"
        ) as f:
            pyproject = tomli.load(f)
            spec = pyproject["tool"]["xapian"]
            return cls(
                version=spec["version"],
                core_sha1=spec["core-sha1"],
                bindings_sha1=spec["bindings-sha1"],
            )


class Command(BaseCommand):
    help = "Install xapian"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Force installation even if already installed",
        )

    def _current_version(self) -> str | None:
        try:
            import xapian
        except ImportError:
            return None
        return xapian.version_string()

    def handle(self, *args, force: bool, **options):
        if not os.environ.get("VIRTUAL_ENV", None):
            self.stdout.write(
                "No virtual environment detected, this command can't be used"
            )
            return

        desired = XapianSpec.from_pyproject()
        if desired.version == self._current_version():
            if not force:
                self.stdout.write(
                    f"Version {desired.version} is already installed, use --force to re-install"
                )
                return
            self.stdout.write(
                f"Version {desired.version} is already installed, re-installing"
            )
        XapianInstaller(desired, self.stdout, self.stderr).run()
        self.stdout.write("Installation success")


class XapianInstaller:
    def __init__(
        self,
        spec: XapianSpec,
        stdout: OutputWrapper,
        stderr: OutputWrapper,
    ):
        self._version = spec.version
        self._core_sha1 = spec.core_sha1
        self._bindings_sha1 = spec.bindings_sha1

        self._stdout = stdout
        self._stderr = stderr
        self._virtual_env = os.environ.get("VIRTUAL_ENV", None)

        if not self._virtual_env:
            raise RuntimeError("You are not inside a virtual environment")
        self._virtual_env = Path(self._virtual_env)

        self._dest_dir = Path(self._virtual_env) / "packages"
        self._core = f"xapian-core-{self._version}"
        self._bindings = f"xapian-bindings-{self._version}"

    def _setup_env(self):
        os.environ.update(
            {
                "CPATH": "",
                "LIBRARY_PATH": "",
                "CFLAGS": "",
                "LDFLAGS": "",
                "CCFLAGS": "",
                "CXXFLAGS": "",
                "CPPFLAGS": "",
            }
        )

    def _prepare_dest_folder(self):
        shutil.rmtree(self._dest_dir, ignore_errors=True)
        self._dest_dir.mkdir(parents=True)

    def _download(self):
        def download(url: str, dest: Path, sha1_hash: str):
            resp = urllib3.request("GET", url)
            if resp.status != 200:
                raise HTTPException(f"Could not download {url}")
            if hashlib.sha1(resp.data).hexdigest() != sha1_hash:
                raise ValueError(f"File downloaded from {url} is compromised")
            with open(dest, "wb") as f:
                f.write(resp.data)

        self._stdout.write("Downloading source…")

        core = self._dest_dir / f"{self._core}.tar.xz"
        bindings = self._dest_dir / f"{self._bindings}.tar.xz"
        download(
            f"https://oligarchy.co.uk/xapian/{self._version}/{self._core}.tar.xz",
            core,
            "e2b4b4cf6076873ec9402cab7b9a3b71dcf95e20",
        )
        download(
            f"https://oligarchy.co.uk/xapian/{self._version}/{self._bindings}.tar.xz",
            bindings,
            "782f568d2ea3ca751c519a2814a35c7dc86df3a4",
        )
        self._stdout.write("Extracting source …")
        with tarfile.open(core) as tar:
            tar.extractall(self._dest_dir)
        with tarfile.open(bindings) as tar:
            tar.extractall(self._dest_dir)

        os.remove(core)
        os.remove(bindings)

    def _install(self):
        self._stdout.write("Installing Xapian-core…")
        subprocess.run(
            ["./configure", "--prefix", str(self._virtual_env)],
            env=dict(os.environ),
            cwd=self._dest_dir / self._core,
        ).check_returncode()
        subprocess.run(
            [
                "make",
                "-j",
                str(multiprocessing.cpu_count()),
            ],
            env=dict(os.environ),
            cwd=self._dest_dir / self._core,
        ).check_returncode()
        subprocess.run(
            ["make", "install"],
            env=dict(os.environ),
            cwd=self._dest_dir / self._core,
        ).check_returncode()

        self._stdout.write("Installing Xapian-bindings")
        subprocess.run(
            [
                "./configure",
                "--prefix",
                str(self._virtual_env),
                "--with-python3",
                f"XAPIAN_CONFIG={self._virtual_env / 'bin'/'xapian-config'}",
            ],
            env=dict(os.environ),
            cwd=self._dest_dir / self._bindings,
        ).check_returncode()
        subprocess.run(
            [
                "make",
                "-j",
                str(multiprocessing.cpu_count()),
            ],
            env=dict(os.environ),
            cwd=self._dest_dir / self._bindings,
        ).check_returncode()
        subprocess.run(
            ["make", "install"],
            env=dict(os.environ),
            cwd=self._dest_dir / self._bindings,
        ).check_returncode()

    def _post_clean(self):
        shutil.rmtree(self._dest_dir, ignore_errors=True)

    def _test(self):
        subprocess.run([sys.executable, "-c", "import xapian"]).check_returncode()

    def run(self):
        self._setup_env()
        self._prepare_dest_folder()
        self._download()
        self._install()
        self._post_clean()
        self._test()
