import atexit

import pytest

from .composer import start_composer, stop_composer
from .settings import PROCFILE_SERVICE

# it's the first hook loaded by pytest and can only
# be defined in a proper pytest plugin
# To use the composer before pytest-django loads
# we need to define this hook and thus create a proper
# pytest plugin. We can't just use conftest.py


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    """Hook that loads the composer before the pytest-django plugin"""
    if PROCFILE_SERVICE is not None:
        start_composer(PROCFILE_SERVICE)
        _ = atexit.register(stop_composer, procfile=PROCFILE_SERVICE)
