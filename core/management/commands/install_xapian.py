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

import os
import subprocess
from pathlib import Path

import tomli
from django.core.management.base import BaseCommand, CommandParser


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

    def _desired_version(self) -> str:
        with open(
            Path(__file__).parent.parent.parent.parent / "pyproject.toml", "rb"
        ) as f:
            pyproject = tomli.load(f)
            return pyproject["tool"]["xapian"]["version"]

    def handle(self, *args, force: bool, **options):
        if not os.environ.get("VIRTUAL_ENV", None):
            self.stdout.write(
                "No virtual environment detected, this command can't be used"
            )
            return

        desired = self._desired_version()
        if desired == self._current_version():
            if not force:
                self.stdout.write(
                    f"Version {desired} is already installed, use --force to re-install"
                )
                return
            self.stdout.write(f"Version {desired} is already installed, re-installing")
        self.stdout.write(
            f"Installing xapian version {desired} at {os.environ['VIRTUAL_ENV']}"
        )
        subprocess.run(
            [str(Path(__file__).parent / "install_xapian.sh"), desired],
            env=dict(os.environ),
            check=True,
        )
        self.stdout.write("Installation success")
