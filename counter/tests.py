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

import re

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

from core.models import User
from counter.models import Counter


class CounterTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.mde = Counter.objects.filter(name="MDE").first()

    def test_full_click(self):
        response = self.client.post(
            reverse("counter:login", kwargs={"counter_id": self.mde.id}),
            {"username": self.skia.username, "password": "plop"},
        )
        response = self.client.get(
            reverse("counter:details", kwargs={"counter_id": self.mde.id})
        )

        self.assertTrue(
            'class="link-button">S&#39; Kia</button>' in str(response.content)
        )

        counter_token = re.search(
            r'name="counter_token" value="([^"]*)"', str(response.content)
        ).group(1)

        response = self.client.post(
            reverse("counter:details", kwargs={"counter_id": self.mde.id}),
            {"code": "4000k", "counter_token": counter_token},
        )
        location = response.get("location")

        response = self.client.get(response.get("location"))
        self.assertTrue(">Richard Batsbak</" in str(response.content))

        response = self.client.post(
            location,
            {
                "action": "refill",
                "amount": "10",
                "payment_method": "CASH",
                "bank": "OTHER",
            },
        )
        response = self.client.post(location, {"action": "code", "code": "BARB"})
        response = self.client.post(location, {"action": "code", "code": "fin"})

        response_get = self.client.get(response.get("location"))
        self.assertTrue(
            "<p>Client : Richard Batsbak - Nouveau montant : 8.30"
            in str(response_get.content)
        )


class BarmanConnectionTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.krophil = User.objects.get(username="krophil")
        self.skia = User.objects.get(username="skia")
        self.skia.customer.account = 800
        self.krophil.customer.save()
        self.skia.customer.save()

        self.counter = Counter.objects.filter(id=2).first()

    def test_barman_granted(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response_get = self.client.get(
            reverse("counter:details", args=[self.counter.id])
        )

        self.assertTrue("<p>Entrez un code client : </p>" in str(response_get.content))

    def test_counters_list_barmen(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response_get = self.client.get(
            reverse("counter:activity", args=[self.counter.id])
        )

        self.assertTrue(
            '<li><a href="/user/10/">Kro Phil&#39;</a></li>'
            in str(response_get.content)
        )

    def test_barman_denied(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "skia", "password": "plop"},
        )
        response_get = self.client.get(
            reverse("counter:details", args=[self.counter.id])
        )

        self.assertTrue("<p>Merci de vous identifier</p>" in str(response_get.content))

    def test_counters_list_no_barmen(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response_get = self.client.get(
            reverse("counter:activity", args=[self.counter.id])
        )

        self.assertFalse(
            '<li><a href="/user/1/">S&#39; Kia</a></li>' in str(response_get.content)
        )
