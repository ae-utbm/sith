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
import json
import re
import string

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import timedelta

from club.models import Club
from core.models import User
from counter.models import BillingInfo, Counter, Customer, Permanency, Product, Selling
from sith.settings import SITH_MAIN_CLUB


class CounterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.filter(username="skia").first()
        cls.sli = User.objects.filter(username="sli").first()
        cls.krophil = User.objects.filter(username="krophil").first()
        cls.mde = Counter.objects.filter(name="MDE").first()
        cls.foyer = Counter.objects.get(id=2)

    def test_full_click(self):
        self.client.post(
            reverse("counter:login", kwargs={"counter_id": self.mde.id}),
            {"username": self.skia.username, "password": "plop"},
        )
        response = self.client.get(
            reverse("counter:details", kwargs={"counter_id": self.mde.id})
        )

        assert 'class="link-button">S&#39; Kia</button>' in str(response.content)

        counter_token = re.search(
            r'name="counter_token" value="([^"]*)"', str(response.content)
        ).group(1)

        response = self.client.post(
            reverse("counter:details", kwargs={"counter_id": self.mde.id}),
            {"code": "4000k", "counter_token": counter_token},
        )
        counter_url = response.get("location")
        response = self.client.get(response.get("location"))
        assert ">Richard Batsbak</" in str(response.content)

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
        self.client.post(
            counter_url, "action=add_product&product_id=4", content_type="text/xml"
        )
        self.client.post(
            counter_url, "action=del_product&product_id=4", content_type="text/xml"
        )
        self.client.post(
            counter_url, "action=code&code=2xdeco", content_type="text/xml"
        )
        self.client.post(
            counter_url, "action=code&code=1xbarb", content_type="text/xml"
        )
        response = self.client.post(
            counter_url, "action=code&code=fin", content_type="text/xml"
        )

        response_get = self.client.get(response.get("location"))
        response_content = response_get.content.decode("utf-8")
        assert "2 x Barbar" in str(response_content)
        assert "2 x Déconsigne Eco-cup" in str(response_content)
        assert "<p>Client : Richard Batsbak - Nouveau montant : 3.60" in str(
            response_content
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
        assert response.status_code == 200

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
        assert response.status_code == 200

    def test_annotate_has_barman_queryset(self):
        """
        Test if the custom queryset method ``annotate_has_barman``
        works as intended
        """
        self.sli.counters.set([self.foyer, self.mde])
        counters = Counter.objects.annotate_has_barman(self.sli)
        for counter in counters:
            if counter.name in ("Foyer", "MDE"):
                assert counter.has_annotated_barman
            else:
                assert not counter.has_annotated_barman


class CounterStatsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.counter = Counter.objects.get(id=2)
        cls.krophil = User.objects.get(username="krophil")
        cls.skia = User.objects.get(username="skia")
        cls.sli = User.objects.get(username="sli")
        cls.root = User.objects.get(username="root")
        cls.subscriber = User.objects.get(username="subscriber")
        cls.old_subscriber = User.objects.get(username="old_subscriber")
        cls.counter.sellers.add(cls.sli, cls.root, cls.skia, cls.krophil)

        barbar = Product.objects.get(code="BARB")

        # remove everything to make sure the fixtures bring no side effect
        Permanency.objects.all().delete()
        Selling.objects.all().delete()

        now = timezone.now()
        # total of sli : 5 hours
        Permanency.objects.create(
            user=cls.sli, start=now, end=now + timedelta(hours=1), counter=cls.counter
        )
        Permanency.objects.create(
            user=cls.sli,
            start=now + timedelta(hours=4),
            end=now + timedelta(hours=6),
            counter=cls.counter,
        )
        Permanency.objects.create(
            user=cls.sli,
            start=now + timedelta(hours=7),
            end=now + timedelta(hours=9),
            counter=cls.counter,
        )

        # total of skia : 16 days, 2 hours, 35 minutes and 54 seconds
        Permanency.objects.create(
            user=cls.skia, start=now, end=now + timedelta(hours=1), counter=cls.counter
        )
        Permanency.objects.create(
            user=cls.skia,
            start=now + timedelta(days=4, hours=1),
            end=now + timedelta(days=20, hours=2, minutes=35, seconds=54),
            counter=cls.counter,
        )

        # total of root : 1 hour + 20 hours (but the 20 hours were on last year)
        Permanency.objects.create(
            user=cls.root,
            start=now + timedelta(days=5),
            end=now + timedelta(days=5, hours=1),
            counter=cls.counter,
        )
        Permanency.objects.create(
            user=cls.root,
            start=now - timedelta(days=300, hours=20),
            end=now - timedelta(days=300),
            counter=cls.counter,
        )

        # total of krophil : 0 hour
        s = Selling(
            label=barbar.name,
            product=barbar,
            club=Club.objects.get(name=SITH_MAIN_CLUB["name"]),
            counter=cls.counter,
            unit_price=2,
            seller=cls.skia,
        )

        krophil_customer = Customer.get_or_create(cls.krophil)[0]
        sli_customer = Customer.get_or_create(cls.sli)[0]
        skia_customer = Customer.get_or_create(cls.skia)[0]
        root_customer = Customer.get_or_create(cls.root)[0]

        # moderate drinker. Total : 100 €
        s.quantity = 50
        s.customer = krophil_customer
        s.save(allow_negative=True)

        # Sli is a drunkard. Total : 2000 €
        s.quantity = 100
        s.customer = sli_customer
        for _ in range(10):
            # little trick to make sure the instance is duplicated in db
            s.pk = None
            s.save(allow_negative=True)  # save ten different sales

        # Skia is a heavy drinker too. Total : 1000 €
        s.customer = skia_customer
        for _ in range(5):
            s.pk = None
            s.save(allow_negative=True)

        # Root is quite an abstemious one. Total : 2 €
        s.pk = None
        s.quantity = 1
        s.customer = root_customer
        s.save(allow_negative=True)

    def test_not_authenticated_user_fail(self):
        # Test with not login user
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        assert response.status_code == 403

    def test_unauthorized_user_fails(self):
        self.client.force_login(User.objects.get(username="public"))
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        assert response.status_code == 403

    def test_get_total_sales(self):
        """
        Test the result of the Counter.get_total_sales() method
        """
        assert self.counter.get_total_sales() == 3102

    def test_top_barmen(self):
        """
        Test the result of Counter.get_top_barmen() is correct
        """
        users = [self.skia, self.root, self.sli]
        perm_times = [
            timedelta(days=16, hours=2, minutes=35, seconds=54),
            timedelta(hours=21),
            timedelta(hours=5),
        ]
        assert list(self.counter.get_top_barmen()) == [
            {
                "user": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "promo": user.promo,
                "nickname": user.nick_name,
                "perm_sum": perm_time,
            }
            for user, perm_time in zip(users, perm_times)
        ]

    def test_top_customer(self):
        """
        Test the result of Counter.get_top_customers() is correct
        """
        users = [self.sli, self.skia, self.krophil, self.root]
        sale_amounts = [2000, 1000, 100, 2]
        assert list(self.counter.get_top_customers()) == [
            {
                "user": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "promo": user.promo,
                "nickname": user.nick_name,
                "selling_sum": sale_amount,
            }
            for user, sale_amount in zip(users, sale_amounts)
        ]


class BillingInfoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        cls.root = User.objects.get(username="root")
        cls.subscriber = User.objects.get(username="subscriber")

    def test_edit_infos(self):
        user = self.subscriber
        BillingInfo.objects.get_or_create(
            customer=user.customer, defaults=self.payload_1
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        assert response.status_code == 200
        self.assertJSONEqual(response.content, {"errors": None})
        assert hasattr(user.customer, "billing_infos")
        assert infos.customer == user.customer
        assert infos.first_name == "Subscribed"
        assert infos.last_name == "User"
        assert infos.address_1 == "3, rue de Troyes"
        assert infos.address_2 is None
        assert infos.zip_code == "34301"
        assert infos.city == "Sète"
        assert infos.country == "FR"

    def test_create_infos_for_user_with_account(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user.customer, "billing_infos"):
            user.customer.billing_infos.delete()
        self.client.force_login(user)
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(self.payload_1),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        assert response.status_code == 200
        self.assertJSONEqual(response.content, {"errors": None})
        assert hasattr(user.customer, "billing_infos")
        assert infos.customer == user.customer
        assert infos.first_name == "Subscribed"
        assert infos.last_name == "User"
        assert infos.address_1 == "1 rue des Huns"
        assert infos.address_2 is None
        assert infos.zip_code == "90000"
        assert infos.city == "Belfort"
        assert infos.country == "FR"

    def test_create_infos_for_user_without_account(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user, "customer"):
            user.customer.delete()
        self.client.force_login(user)
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(self.payload_1),
            content_type="application/json",
        )
        user = User.objects.get(username="subscriber")
        assert hasattr(user, "customer")
        assert hasattr(user.customer, "billing_infos")
        assert response.status_code == 200
        self.assertJSONEqual(response.content, {"errors": None})
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertEqual(user.customer, infos.customer)
        assert infos.first_name == "Subscribed"
        assert infos.last_name == "User"
        assert infos.address_1 == "1 rue des Huns"
        assert infos.address_2 is None
        assert infos.zip_code == "90000"
        assert infos.city == "Belfort"
        assert infos.country == "FR"

    def test_create_invalid(self):
        user = User.objects.get(username="subscriber")
        if hasattr(user.customer, "billing_infos"):
            user.customer.billing_infos.delete()
        self.client.force_login(user)
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
        assert not hasattr(user.customer, "billing_infos")
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
        self.client.force_login(user)
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
        assert hasattr(user.customer, "billing_infos")
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
        self.client.force_login(user)
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
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("counter:edit_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        assert response.status_code == 200
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertJSONEqual(response.content, {"errors": None})
        assert hasattr(user.customer, "billing_infos")
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
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("counter:create_billing_info", args=[user.id]),
            json.dumps(self.payload_2),
            content_type="application/json",
        )
        assert response.status_code == 200
        user = User.objects.get(username="subscriber")
        infos = BillingInfo.objects.get(customer__user=user)
        self.assertJSONEqual(response.content, {"errors": None})
        assert hasattr(user.customer, "billing_infos")
        assert infos.customer == user.customer
        assert infos.first_name == "Subscribed"
        assert infos.last_name == "User"
        assert infos.address_1 == "3, rue de Troyes"
        assert infos.address_2 is None
        assert infos.zip_code == "34301"
        assert infos.city == "Sète"
        assert infos.country == "FR"


class BarmanConnectionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.krophil = User.objects.get(username="krophil")
        cls.skia = User.objects.get(username="skia")
        cls.skia.customer.account = 800
        cls.krophil.customer.save()
        cls.skia.customer.save()

        cls.counter = Counter.objects.get(id=2)

    def test_barman_granted(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response = self.client.get(reverse("counter:details", args=[self.counter.id]))

        assert "<p>Entrez un code client : </p>" in str(response.content)

    def test_counters_list_barmen(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response = self.client.get(reverse("counter:activity", args=[self.counter.id]))

        assert '<li><a href="/user/10/">Kro Phil&#39;</a></li>' in str(response.content)

    def test_barman_denied(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "skia", "password": "plop"},
        )
        response_get = self.client.get(
            reverse("counter:details", args=[self.counter.id])
        )

        assert "<p>Merci de vous identifier</p>" in str(response_get.content)

    def test_counters_list_no_barmen(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response = self.client.get(reverse("counter:activity", args=[self.counter.id]))

        assert not '<li><a href="/user/1/">S&#39; Kia</a></li>' in str(response.content)


class StudentCardTest(TestCase):
    """
    Tests for adding and deleting Stundent Cards
    Test that an user can be found with it's student card
    """

    @classmethod
    def setUpTestData(cls):
        cls.krophil = User.objects.get(username="krophil")
        cls.sli = User.objects.get(username="sli")
        cls.skia = User.objects.get(username="skia")
        cls.root = User.objects.get(username="root")

        cls.counter = Counter.objects.get(id=2)

    def setUp(self):
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

        assert response.url == reverse(
            "counter:click",
            kwargs={"counter_id": self.counter.id, "user_id": self.sli.id},
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
        self.client.force_login(self.sli)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        assert not self.sli.customer.student_cards.exists()

    def test_delete_student_card_with_board_member(self):
        self.client.force_login(self.skia)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        assert not self.sli.customer.student_cards.exists()

    def test_delete_student_card_with_root(self):
        self.client.force_login(self.root)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        assert not self.sli.customer.student_cards.exists()

    def test_delete_student_card_fail(self):
        self.client.force_login(self.krophil)
        response = self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.sli.customer.pk,
                    "card_id": self.sli.customer.student_cards.first().id,
                },
            )
        )
        assert response.status_code == 403
        assert self.sli.customer.student_cards.exists()

    def test_add_student_card_from_user_preferences(self):
        # Test with owner of the card
        self.client.force_login(self.sli)
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
        self.client.force_login(self.skia)
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
        self.client.force_login(self.root)
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
        self.client.force_login(self.sli)
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
            {"uid": " " * 14},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with unauthorized user
        self.client.force_login(self.krophil)
        response = self.client.post(
            reverse(
                "counter:add_student_card", kwargs={"customer_id": self.sli.customer.pk}
            ),
            {"uid": "8B90734A802A8F"},
        )
        assert response.status_code == 403


class CustomerAccountIdTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create(
            username="a", password="plop", email="a.a@a.fr"
        )
        user_b = User.objects.create(username="b", password="plop", email="b.b@b.fr")
        user_c = User.objects.create(username="c", password="plop", email="c.c@c.fr")
        Customer.objects.create(user=cls.user_a, amount=10, account_id="1111a")
        Customer.objects.create(user=user_b, amount=0, account_id="9999z")
        Customer.objects.create(user=user_c, amount=0, account_id="12345f")

    def test_create_customer(self):
        user_d = User.objects.create(username="d", password="plop")
        customer, created = Customer.get_or_create(user_d)
        account_id = customer.account_id
        number = account_id[:-1]
        assert created is True
        assert number == "12346"
        assert 6 == len(account_id)
        assert account_id[-1] in string.ascii_lowercase
        assert customer.amount == 0

    def test_get_existing_account(self):
        account, created = Customer.get_or_create(self.user_a)
        assert created is False
        assert account.account_id == "1111a"
        assert account.amount == 10
