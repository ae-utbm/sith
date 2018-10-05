# -*- coding:utf-8 -*
#
# Copyright 2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

import sys

from django.apps import AppConfig
from django.core.signals import request_started


class SithConfig(AppConfig):
    name = "core"
    verbose_name = "Core app of the Sith"

    def ready(self):
        from core.models import User
        from club.models import Club
        from forum.models import Forum

        def clear_cached_groups(**kwargs):
            User._group_ids = {}
            User._group_name = {}

        def clear_cached_memberships(**kwargs):
            User._club_memberships = {}
            Club._memberships = {}
            Forum._club_memberships = {}

        print("Connecting signals!", file=sys.stderr)
        request_started.connect(
            clear_cached_groups, weak=False, dispatch_uid="clear_cached_groups"
        )
        request_started.connect(
            clear_cached_memberships,
            weak=False,
            dispatch_uid="clear_cached_memberships",
        )
        # TODO: there may be a need to add more cache clearing
