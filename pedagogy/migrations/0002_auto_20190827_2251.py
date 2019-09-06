# -*- coding:utf-8 -*
#
# Copyright 2019
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
