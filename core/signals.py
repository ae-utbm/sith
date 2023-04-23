# -*- coding:utf-8 -*
#
# Copyright 2023
# - Maréchal <thgirod@hotmail.com>
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


from django.core.cache import cache
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from club.models import Club, Membership
from core.models import Group


@receiver(pre_delete, sender=Club, dispatch_uid="clear_cached_memberships")
def clear_cached_memberships(sender, instance: Club, **_kwargs):
    """
    When a club is deleted, clear the cache of the memberships
    associated with this club
    """
    for membership in instance.members.ongoing():
        cache.delete(f"membership_{membership.club.id}_{membership.user.id}")


@receiver(
    pre_delete,
    sender=Group,
    dispatch_uid="clear_cached_user_groups",
)
def clear_cached_user_groups(sender, instance: Group, **_kwargs):
    """
    When the membership of a user is deleted or edited, clear the associated cache
    """
    cache.delete(f"sith_group_{instance.id}")
    cache.delete(f"sith_group_{instance.name.replace(' ', '_')}")
