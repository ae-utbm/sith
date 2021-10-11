#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Copyright 2017
# - Sli <antoine@bartuccio.fr>
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

from django.core.management.base import BaseCommand

from core.models import User
from rootplace.views import delete_all_forum_user_messages


class Command(BaseCommand):
    """
    Delete all forum messages from a user
    """

    help = "Delete all user's forum message"

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):

        user = User.objects.filter(id=options["user_id"]).first()

        if user is None:
            print("User with ID %s not found" % (options["user_id"],))
            exit(1)

        confirm = input(
            "User selected: %s\nDo you really want to delete all message from this user ? [y/N] "
            % (user,)
        )

        if not confirm.lower().startswith("y"):
            print("Operation aborted")
            exit(1)

        delete_all_forum_user_messages(user, User.objects.get(id=0), True)
