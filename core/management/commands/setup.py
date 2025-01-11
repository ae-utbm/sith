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

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Set up the development environment."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise Exception("Never call this command in prod. Never.")
        data_dir = settings.BASE_DIR / "data"
        settings.EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
        if not data_dir.is_dir():
            data_dir.mkdir()
        db_path = settings.BASE_DIR / "db.sqlite3"
        if db_path.exists() or connection.vendor != "sqlite":
            call_command("flush", "--noinput")
            self.stdout.write("Existing database reset")
        call_command("migrate")
        self.stdout.write("Add the base fixtures.")
        call_command("populate")
        self.stdout.write("Generate additional random fixtures")
        call_command("populate_more")
        self.stdout.write("Build the xapian index")
        call_command("rebuild_index", "--noinput")

        settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        self.stdout.write("Setup complete!")
