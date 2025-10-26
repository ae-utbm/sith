import contextlib
import os

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_populate_more(settings):
    """Just check that populate more doesn't crash"""
    settings.DEBUG = True
    with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull):
        call_command("populate_more", "--nb-users", "50")
