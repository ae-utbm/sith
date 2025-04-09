#!/usr/bin/env python3
#
# Copyright 2023 © AE UTBM
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
import atexit
import logging
import os
import sys

from django.conf import settings
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from sith.composer import start_composer, stop_composer

if __name__ == "__main__":
    logging.basicConfig(encoding="utf-8", level=logging.INFO)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sith.settings")

    from django.core.management import execute_from_command_line

    if (
        os.environ.get(DJANGO_AUTORELOAD_ENV) is None
        and settings.PROCFILE_SERVICE is not None
    ):
        start_composer(settings.PROCFILE_SERVICE)
        _ = atexit.register(stop_composer, procfile=settings.PROCFILE_SERVICE)

    execute_from_command_line(sys.argv)
