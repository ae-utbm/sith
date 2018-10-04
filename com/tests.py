# -*- coding:utf-8 -*
#
# Copyright 2016,2017
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

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.management import call_command

from core.models import User, RealGroup


class ComTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.com_group = RealGroup.objects.filter(
            id=settings.SITH_GROUP_COM_ADMIN_ID
        ).first()
        self.skia.groups = [self.com_group]
        self.skia.save()
        self.client.login(username=self.skia.username, password="plop")

    def test_alert_msg(self):
        response = self.client.post(
            reverse("com:alert_edit"),
            {
                "alert_msg": """
### ALERTE!

**Caaaataaaapuuuulte!!!!**
"""
            },
        )
        r = self.client.get(reverse("core:index"))
        self.assertTrue(r.status_code == 200)
        self.assertTrue(
            """<div id="alert_box">\\n                <div class="markdown"><h3>ALERTE!</h3>\\n<p><strong>Caaaataaaapuuuulte!!!!</strong></p>"""
            in str(r.content)
        )

    def test_info_msg(self):
        response = self.client.post(
            reverse("com:info_edit"),
            {
                "info_msg": """
### INFO: **Caaaataaaapuuuulte!!!!**
"""
            },
        )
        r = self.client.get(reverse("core:index"))
        self.assertTrue(r.status_code == 200)
        self.assertTrue(
            """<div id="info_box">\\n                <div class="markdown"><h3>INFO: <strong>Caaaataaaapuuuulte!!!!</strong></h3>"""
            in str(r.content)
        )
