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

from __future__ import unicode_literals

from django.db import migrations

from core.models import User


def remove_multiples_comments_from_same_user(apps, schema_editor):
    for user in User.objects.exclude(uv_comments=None).prefetch_related("uv_comments"):
        for uv in user.uv_comments.values("uv").distinct():
            last = (
                user.uv_comments.filter(uv__id=uv["uv"])
                .order_by("-publish_date")
                .first()
            )
            for comment in (
                user.uv_comments.filter(uv__id=uv["uv"]).exclude(pk=last.pk).all()
            ):
                print("removing : %s" % (comment,))
                comment.delete()


class Migration(migrations.Migration):
    dependencies = [("pedagogy", "0001_initial")]

    operations = [
        migrations.RunPython(
            remove_multiples_comments_from_same_user,
            reverse_code=migrations.RunPython.noop,
        )
    ]
