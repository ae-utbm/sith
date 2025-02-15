import logging
import os
import subprocess
import sys

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as Runserver,
)
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from staticfiles.processors import OpenApi


class Command(Runserver):
    """Light wrapper around default runserver that integrates javascirpt auto bundling."""

    def run(self, **options):
        # OpenApi generation needs to be before the bundler
        OpenApi.compile()
        # Run all other web processes but only if debug mode is enabled
        # Also protects from re-launching the server if django reloads it
        if os.environ.get(DJANGO_AUTORELOAD_ENV) is None:
            logging.getLogger("django").info("Running complementary processes")
            with subprocess.Popen(
                [sys.executable, "-m", "honcho", "start"],
                env={
                    **os.environ,
                    **{"BUNDLER_MODE": "serve" if settings.DEBUG else "compile"},
                },
            ):
                super().run(**options)
                return
        super().run(**options)
