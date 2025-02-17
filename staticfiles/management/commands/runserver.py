from django.contrib.staticfiles.management.commands.runserver import (
    Command as Runserver,
)

from staticfiles.processors import OpenApi


class Command(Runserver):
    """Light wrapper around default runserver that integrates javascirpt auto bundling."""

    def run(self, **options):
        OpenApi.compile()
        super().run(**options)
