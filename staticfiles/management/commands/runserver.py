import os

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as Runserver,
)
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from staticfiles.processors import JSBundler, OpenApi


class Command(Runserver):
    """Light wrapper around default runserver that integrates javascirpt auto bundling."""

    def run(self, **options):
        # OpenApi generation needs to be before the bundler
        OpenApi.compile()
        # Only run the bundling server when debug is enabled
        # Also protects from re-launching the server if django reloads it
        if os.environ.get(DJANGO_AUTORELOAD_ENV) is None and settings.DEBUG:
            with JSBundler.runserver():
                super().run(**options)
                return
        super().run(**options)
