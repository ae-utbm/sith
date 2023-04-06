# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

import sys

from django.apps import AppConfig
from django.core.cache import cache
from django.core.signals import request_started


class SithConfig(AppConfig):
    name = "core"
    verbose_name = "Core app of the Sith"

    def ready(self):
        import core.signals  # noqa F401
        from forum.models import Forum

        cache.clear()

        def clear_cached_memberships(**kwargs):
            Forum._club_memberships = {}

        print("Connecting signals!", file=sys.stderr)
        request_started.connect(
            clear_cached_memberships,
            weak=False,
            dispatch_uid="clear_cached_memberships",
        )
