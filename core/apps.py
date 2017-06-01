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

from django.apps import AppConfig
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, m2m_changed

class SithConfig(AppConfig):
    name = 'core'
    verbose_name = "Core app of the Sith"

    def ready(self):
        from core.models import User, Group
        from club.models import Club, Membership
        from forum.models import Forum

        def clear_cached_groups(sender, **kwargs):
            if kwargs['model'] == Group:
                User._group_ids = {}
                User._group_name = {}

        def clear_cached_memberships(sender, **kwargs):
            User._club_memberships = {}
            Club._memberships = {}
            Forum._club_memberships = {}

        print("Connecting signals!")
        m2m_changed.connect(clear_cached_groups, weak=False, dispatch_uid="clear_cached_groups")
        post_save.connect(clear_cached_memberships, weak=False, sender=Membership, # Membership is cached
                dispatch_uid="clear_cached_memberships_membership")
        post_save.connect(clear_cached_memberships, weak=False, sender=Club, # Club has a cache of Membership
                dispatch_uid="clear_cached_memberships_club")
        post_save.connect(clear_cached_memberships, weak=False, sender=Forum, # Forum has a cache of Membership
                dispatch_uid="clear_cached_memberships_forum")
        # TODO: there may be a need to add more cache clearing

