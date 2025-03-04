import atexit
import os

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as Runserver,
)
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from sith.composer import start_composer, stop_composer
from staticfiles.processors import OpenApi


class Command(Runserver):
    """Light wrapper around default runserver that integrates javascirpt auto bundling."""

    def run(self, **options):
        OpenApi.compile()
        if (
            os.environ.get(DJANGO_AUTORELOAD_ENV) is None
            and settings.PROCFILE_STATIC is not None
        ):
            start_composer(settings.PROCFILE_STATIC)
            _ = atexit.register(stop_composer, procfile=settings.PROCFILE_STATIC)
        super().run(**options)
