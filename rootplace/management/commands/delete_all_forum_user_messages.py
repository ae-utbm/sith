#!/usr/bin/env python3
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
