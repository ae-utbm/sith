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
import json
import re

from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command

from core.models import User
from counter.models import Counter, Customer, BillingInfo


class CounterTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.sli = User.objects.filter(username="sli").first()
        self.krophil = User.objects.filter(username="krophil").first()
        self.mde = Counter.objects.filter(name="MDE").first()
        self.foyer = Counter.objects.get(id=2)

    def test_full_click(self):
        self.client.post(
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
        counter_url = response.get("location")
        response = self.client.get(response.get("location"))
        self.assertTrue(">Richard Batsbak</" in str(response.content))

        self.client.post(
            counter_url,
            {
                "action": "refill",
                "amount": "5",
                "payment_method": "CASH",
                "bank": "OTHER",
            },
        )
        self.client.post(counter_url, "action=code&code=BARB", content_type="text/xml")
        self.client.post(counter_url, "action=add_product&product_id=4", content_type="text/xml")
        self.client.post(counter_url, "action=del_product&product_id=4", content_type="text/xml")
        self.client.post(counter_url, "action=code&code=2xdeco", content_type="text/xml")
        self.client.post(counter_url, "action=code&code=1xbarb", content_type="text/xml")
        response = self.client.post(counter_url, "action=code&code=fin", content_type="text/xml")

        response_get = self.client.get(response.get("location"))
        response_content = response_get.content.decode("utf-8")
        self.assertTrue("2 x Barbar" in str(response_content))
        self.assertTrue("2 x Déconsigne Eco-cup" in str(response_content))
        self.assertTrue(
            "<p>Client : Richard Batsbak - Nouveau montant : 3.60"
            in str(response_content)
        )

        self.client.post(
            reverse("counter:login", kwargs={"counter_id": self.mde.id}),
            {"username": self.sli.username, "password": "plop"},
        )

        response = self.client.post(
            counter_url,
            {
                "action": "refill",
                "amount": "5",
                "payment_method": "CASH",
                "bank": "OTHER",
            },
        )
        self.assertTrue(response.status_code == 200)

        self.client.post(
            reverse("counter:login", kwargs={"counter_id": self.foyer.id}),
            {"username": self.krophil.username, "password": "plop"},
        )

        response = self.client.get(
            reverse("counter:details", kwargs={"counter_id": self.foyer.id})
        )

        counter_token = re.search(
            r'name="counter_token" value="([^"]*)"', str(response.content)
        ).group(1)

        response = self.client.post(
            reverse("counter:details", kwargs={"counter_id": self.foyer.id}),
            {"code": "4000k", "counter_token": counter_token},
        )
        counter_url = response.get("location")

        response = self.client.post(
            counter_url,
            {
                "action": "refill",
                "amount": "5",
                "payment_method": "CASH",
                "bank": "OTHER",
            },
        )
        self.assertTrue(response.status_code == 200)


class CounterStatsTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.counter = Counter.objects.filter(id=2).first()

    def test_unauthorised_user_fail(self):
        # Test with not login user
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        self.assertTrue(response.status_code == 403)


class BillingInfoTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload_1 = {
            "first_name": "Subscribed",
            "last_name": "User",
            "address_1": "1 rue des Huns",
            "zip_code": "90000",
            "city": "Belfort",
            "country": "FR",
        }
        cls.payload_2 = {
            "first_name": "Subscribed",
            "last_name": "User",
            "address_1": "3, rue de Troyes",
            "zip_code": "34301",
            "city": "Sète",
            "country": "FR",
        }
        super().setUpClass()
        call_command("populate")

    def test_edit_infos(self):
        user = User.objects.get(username="subscriber")
        BillingInfo.objects.get_or_create(
            customer=user.customer, defaults=self.payload_1
        )
        self.client.login(username=user.username, password="plop")
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(response.content, {"errors": None})
        self.assertTrue(hasattr(user.customer, "billing_infos"))
        self.assertEqual(user.customer, infos.customer)
        self.assertEqual("Subscribed", infos.first_name)
        self.assertEqual("User", infos.last_name)
        self.assertEqual("3, rue de Troyes", infos.address_1)
        self.assertEqual(None, infos.address_2)
        self.assertEqual("34301", infos.zip_code)
        self.assertEqual("Sète", infos.city)
        self.assertEqual("FR", infos.country)

    def test_create_infos_for_user_with_account(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user.customer, "billing_infos"):
            user.customer.billing_infos.delete()
        self.client.login(username=user.username, password="plop")
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(self.payload_1),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(response.content, {"errors": None})
        self.assertTrue(hasattr(user.customer, "billing_infos"))
        self.assertEqual(user.customer, infos.customer)
        self.assertEqual("Subscribed", infos.first_name)
        self.assertEqual("User", infos.last_name)
        self.assertEqual("1 rue des Huns", infos.address_1)
        self.assertEqual(None, infos.address_2)
        self.assertEqual("90000", infos.zip_code)
        self.assertEqual("Belfort", infos.city)
        self.assertEqual("FR", infos.country)

    def test_create_infos_for_user_without_account(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user, "customer"):
            user.customer.delete()
        self.client.login(username=user.username, password="plop")
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(self.payload_1),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        self.assertTrue(hasattr(user, "customer"))
        self.assertTrue(hasattr(user.customer, "billing_infos"))
        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(response.content, {"errors": None})
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertEqual(user.customer, infos.customer)
        self.assertEqual("Subscribed", infos.first_name)
        self.assertEqual("User", infos.last_name)
        self.assertEqual("1 rue des Huns", infos.address_1)
        self.assertEqual(None, infos.address_2)
        self.assertEqual("90000", infos.zip_code)
        self.assertEqual("Belfort", infos.city)
        self.assertEqual("FR", infos.country)

    def test_create_invalid(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user.customer, "billing_infos"):
            user.customer.billing_infos.delete()
        self.client.login(username=user.username, password="plop")
        # address_1, zip_code and country are missing
        payload = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "city": "Belfort",
        }
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        self.assertEqual(400, response.status_code)
        self.assertFalse(hasattr(user.customer, "billing_infos"))
        expected_errors = {
            "errors": [
                {"field": "Adresse 1", "messages": ["Ce champ est obligatoire."]},
                {"field": "Code postal", "messages": ["Ce champ est obligatoire."]},
                {"field": "Country", "messages": ["Ce champ est obligatoire."]},
            ]
        }
        self.assertJSONEqual(response.content, expected_errors)

    def test_edit_invalid(self):
        user = User.objects.get(username="subscriber")
        BillingInfo.objects.get_or_create(
            customer=user.customer, defaults=self.payload_1
        )
        self.client.login(username=user.username, password="plop")
        # address_1, zip_code and country are missing
        payload = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "city": "Belfort",
        }
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        self.assertEqual(400, response.status_code)
        self.assertTrue(hasattr(user.customer, "billing_infos"))
        expected_errors = {
            "errors": [
                {"field": "Adresse 1", "messages": ["Ce champ est obligatoire."]},
                {"field": "Code postal", "messages": ["Ce champ est obligatoire."]},
                {"field": "Country", "messages": ["Ce champ est obligatoire."]},
            ]
        }
        self.assertJSONEqual(response.content, expected_errors)

    def test_edit_other_user(self):
        user = User.objects.get(username="sli")
        self.client.login(username="subscriber", password="plop")
        BillingInfo.objects.get_or_create(
            customer=user.customer, defaults=self.payload_1
        )
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)

    def test_edit_not_existing_infos(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user.customer, "billing_infos"):
            user.customer.billing_infos.delete()
        self.client.login(username=user.username, password="plop")
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        self.assertEqual(404, response.status_code)

    def test_edit_by_root(self):
        user = User.objects.get(username="subscriber")
        BillingInfo.objects.get_or_create(
            customer=user.customer, defaults=self.payload_1
        )
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertJSONEqual(response.content, {"errors": None})
        self.assertTrue(hasattr(user.customer, "billing_infos"))
        self.assertEqual(user.customer, infos.customer)
        self.assertEqual("Subscribed", infos.first_name)
        self.assertEqual("User", infos.last_name)
        self.assertEqual("3, rue de Troyes", infos.address_1)
        self.assertEqual(None, infos.address_2)
        self.assertEqual("34301", infos.zip_code)
        self.assertEqual("Sète", infos.city)
        self.assertEqual("FR", infos.country)

    def test_create_by_root(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user.customer, "billing_infos"):
            user.customer.billing_infos.delete()
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertJSONEqual(response.content, {"errors": None})
        self.assertTrue(hasattr(user.customer, "billing_infos"))
        self.assertEqual(user.customer, infos.customer)
        self.assertEqual("Subscribed", infos.first_name)
        self.assertEqual("User", infos.last_name)
        self.assertEqual("3, rue de Troyes", infos.address_1)
        self.assertEqual(None, infos.address_2)
        self.assertEqual("34301", infos.zip_code)
        self.assertEqual("Sète", infos.city)
        self.assertEqual("FR", infos.country)


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


class StudentCardTest(TestCase):
    """
    Tests for adding and deleting Stundent Cards
    Test that an user can be found with it's student card
    """

    def setUp(self):
        call_command("populate")
        self.krophil = User.objects.get(username="krophil")
        self.sli = User.objects.get(username="sli")

        self.counter = Counter.objects.filter(id=2).first()

        # Auto login on counter
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )

    def test_search_user_with_student_card(self):
        response = self.client.post(
            reverse("counter:details", args=[self.counter.id]),
            {"code": "9A89B82018B0A0"},
        )

        self.assertEqual(
            response.url,
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
        )

    def test_add_student_card_from_counter(self):
        # Test card with mixed letters and numbers
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "8B90734A802A8F", "action": "add_student_card"},
        )
        self.assertContains(response, text="8B90734A802A8F")

        # Test card with only numbers
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "04786547890123", "action": "add_student_card"},
        )
        self.assertContains(response, text="04786547890123")

        # Test card with only letters
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "ABCAAAFAAFAAAB", "action": "add_student_card"},
        )
        self.assertContains(response, text="ABCAAAFAAFAAAB")

    def test_add_student_card_from_counter_fail(self):
        # UID too short
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "8B90734A802A8", "action": "add_student_card"},
        )
        self.assertContains(
            response, text="Ce n'est pas un UID de carte étudiante valide"
        )

        # UID too long
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "8B90734A802A8FA", "action": "add_student_card"},
        )
        self.assertContains(
            response, text="Ce n'est pas un UID de carte étudiante valide"
        )

        # Test with already existing card
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "9A89B82018B0A0", "action": "add_student_card"},
        )
        self.assertContains(
            response, text="Ce n'est pas un UID de carte étudiante valide"
        )

        # Test with lowercase
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "8b90734a802a9f", "action": "add_student_card"},
        )
        self.assertContains(
            response, text="Ce n'est pas un UID de carte étudiante valide"
        )

        # Test with white spaces
        response = self.client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
            ),
            {"student_card_uid": "              ", "action": "add_student_card"},
        )
        self.assertContains(
            response, text="Ce n'est pas un UID de carte étudiante valide"
        )

    def test_delete_student_card_with_owner(self):
        self.client.login(username="sli", password="plop")
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        self.assertFalse(self.sli.customer.student_cards.exists())

    def test_delete_student_card_with_board_member(self):
        self.client.login(username="skia", password="plop")
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        self.assertFalse(self.sli.customer.student_cards.exists())

    def test_delete_student_card_with_root(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        self.assertFalse(self.sli.customer.student_cards.exists())

    def test_delete_student_card_fail(self):
        self.client.login(username="krophil", password="plop")
        response = self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.sli.customer.student_cards.exists())

    def test_add_student_card_from_user_preferences(self):
        # Test with owner of the card
        self.client.login(username="sli", password="plop")
        self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8F"},
        )

        response = self.client.get(
            reverse("core:user_prefs", kwargs={"user_id": self.sli.id})
        )
        self.assertContains(response, text="8B90734A802A8F")

        # Test with board member
        self.client.login(username="skia", password="plop")
        self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8A"},
        )

        response = self.client.get(
            reverse("core:user_prefs", kwargs={"user_id": self.sli.id})
        )
        self.assertContains(response, text="8B90734A802A8A")

        # Test card with only numbers
        self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "04786547890123"},
        )
        response = self.client.get(
            reverse("core:user_prefs", kwargs={"user_id": self.sli.id})
        )
        self.assertContains(response, text="04786547890123")

        # Test card with only letters
        self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "ABCAAAFAAFAAAB"},
        )
        response = self.client.get(
            reverse("core:user_prefs", kwargs={"user_id": self.sli.id})
        )
        self.assertContains(response, text="ABCAAAFAAFAAAB")

        # Test with root
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8B"},
        )

        response = self.client.get(
            reverse("core:user_prefs", kwargs={"user_id": self.sli.id})
        )
        self.assertContains(response, text="8B90734A802A8B")

    def test_add_student_card_from_user_preferences_fail(self):
        self.client.login(username="sli", password="plop")
        # UID too short
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8"},
        )

        self.assertContains(response, text="Cet UID est invalide")

        # UID too long
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8FA"},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with already existing card
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "9A89B82018B0A0"},
        )
        self.assertContains(
            response, text="Un objet Student card avec ce champ Uid existe déjà."
        )

        # Test with lowercase
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8b90734a802a9f"},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with white spaces
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "              "},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with unauthorized user
        self.client.login(username="krophil", password="plop")
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8F"},
        )
        self.assertEqual(response.status_code, 403)


class AccountIdTest(TestCase):
    def setUp(self):
        user_a = User.objects.create(username="a", password="plop", email="a.a@a.fr")
        user_b = User.objects.create(username="b", password="plop", email="b.b@b.fr")
        user_c = User.objects.create(username="c", password="plop", email="c.c@c.fr")
        Customer.objects.create(user=user_a, amount=0, account_id="1111a")
        Customer.objects.create(user=user_b, amount=0, account_id="9999z")
        Customer.objects.create(user=user_c, amount=0, account_id="12345f")

    def test_create_customer(self):
        user_d = User.objects.create(username="d", password="plop")
        customer_d = Customer.new_for_user(user_d)
        customer_d.save()
        number = customer_d.account_id[:-1]
        self.assertEqual(number, "12346")
