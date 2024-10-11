import os

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as Runserver,
)
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from staticfiles.processors import OpenApi, Webpack


class Command(Runserver):
    """Light wrapper around the statics runserver that integrates webpack auto bundling"""

    def run(self, **options):
        # OpenApi generation needs to be before webpack
        OpenApi.compile()
        # Only run webpack server when debug is enabled
        # Also protects from re-launching the server if django reloads it
        if os.environ.get(DJANGO_AUTORELOAD_ENV) is None and settings.DEBUG:
            with Webpack.runserver():
                super().run(**options)
                return
        super().run(**options)
