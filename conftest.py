import pytest
from django.core.management import call_command
from django.utils.translation import activate


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("setup")


@pytest.fixture(scope="session", autouse=True)
def set_default_language():
    activate('fr')
