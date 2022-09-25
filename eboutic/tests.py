# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Maréchal <thgirod@hotmail.com
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
import base64
import json
import re
import urllib

from OpenSSL import crypto
from django.conf import settings
from django.core.management import call_command
from django.db.models import Max
from django.test import TestCase
from django.urls import reverse

from core.models import User
from counter.models import Product, Counter, Customer, Selling
from eboutic.models import Basket


class EbouticTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.subscriber = User.objects.filter(username="subscriber").first()
        self.old_subscriber = User.objects.filter(username="old_subscriber").first()
        self.public = User.objects.filter(username="public").first()
        self.barbar = Product.objects.filter(code="BARB").first()
        self.refill = Product.objects.filter(code="15REFILL").first()
        self.cotis = Product.objects.filter(code="1SCOTIZ").first()
        self.eboutic = Counter.objects.filter(name="Eboutic").first()

    def get_busy_basket(self, user):
        """
        Create and return a basket with 3 barbar and 1 cotis in it.
        Edit the client session to store the basket id in it
        """
        session = self.client.session
        basket = Basket.objects.create(user=user)
        session["basket_id"] = basket.id
        session.save()
        basket.add_product(self.barbar, 3)
        basket.add_product(self.cotis)
        return basket

    def generate_bank_valid_answer_from_page_content(self, content):
        content = str(content)
        basket_id = re.search(r"PBX_CMD\" value=\"(\d*)\"", content).group(1)
        amount = re.search(r"PBX_TOTAL\" value=\"(\d*)\"", content).group(1)
        query = "Amount=%s&BasketID=%s&Auto=42&Error=00000" % (amount, basket_id)
        with open("./eboutic/tests/private_key.pem") as f:
            PRIVKEY = f.read()
        with open("./eboutic/tests/public_key.pem") as f:
            settings.SITH_EBOUTIC_PUB_KEY = f.read()
        privkey = crypto.load_privatekey(crypto.FILETYPE_PEM, PRIVKEY)
        sig = crypto.sign(privkey, query.encode("utf-8"), "sha1")
        b64sig = base64.b64encode(sig).decode("ascii")

        url = reverse("eboutic:etransation_autoanswer") + "?%s&Sig=%s" % (
            query,
            urllib.parse.quote_plus(b64sig),
        )
        response = self.client.get(url)
        return response

    def test_buy_with_sith_account(self):
        self.client.login(username="subscriber", password="plop")
        self.subscriber.customer.amount = 100  # give money before test
        self.subscriber.customer.save()
        basket = self.get_busy_basket(self.subscriber)
        amount = basket.get_total()
        response = self.client.post(reverse("eboutic:pay_with_sith"))
        self.assertRedirects(response, "/eboutic/pay/success/")
        new_balance = Customer.objects.get(user=self.subscriber).amount
        self.assertEqual(float(new_balance), 100 - amount)
        self.assertEqual(
            'basket_items=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/eboutic',
            self.client.cookies["basket_items"].OutputString(),
        )

    def test_buy_with_sith_account_no_money(self):
        self.client.login(username="subscriber", password="plop")
        basket = self.get_busy_basket(self.subscriber)
        initial = basket.get_total() - 1
        self.subscriber.customer.amount = initial
        self.subscriber.customer.save()
        response = self.client.post(reverse("eboutic:pay_with_sith"))
        self.assertRedirects(response, "/eboutic/pay/failure/")
        new_balance = Customer.objects.get(user=self.subscriber).amount
        self.assertEqual(float(new_balance), initial)
        self.assertEqual(
            'basket_items=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/eboutic',
            self.client.cookies["basket_items"].OutputString(),
        )  # this cookie should be removed after payment

    def test_submit_basket(self):
        self.client.login(username="subscriber", password="plop")
        self.client.cookies[
            "basket_items"
        ] = """[
            {"id": 2, "name": "Cotis 2 semestres", "quantity": 1, "unit_price": 28},
            {"id": 4, "name": "Barbar", "quantity": 3, "unit_price": 1.7}
        ]"""
        response = self.client.post(reverse("eboutic:command"))
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            "<tr><td>Cotis 2 semestres</td><td>1</td><td>28.00 €</td></tr>",
            response.content.decode(),
        )
        self.assertInHTML(
            "<tr><td>Barbar</td><td>3</td><td>1.70 €</td></tr>",
            response.content.decode(),
        )
        self.assertIn("basket_id", self.client.session)
        basket = Basket.objects.get(id=self.client.session["basket_id"])
        self.assertEqual(basket.items.count(), 2)
        barbar = basket.items.filter(product_name="Barbar").first()
        self.assertIsNotNone(barbar)
        self.assertEqual(barbar.quantity, 3)
        cotis = basket.items.filter(product_name="Cotis 2 semestres").first()
        self.assertIsNotNone(cotis)
        self.assertEqual(cotis.quantity, 1)
        self.assertEqual(basket.get_total(), 3 * 1.7 + 28)

    def test_submit_empty_basket(self):
        self.client.login(username="subscriber", password="plop")
        self.client.cookies["basket_items"] = "[]"
        response = self.client.post(reverse("eboutic:command"))
        self.assertRedirects(response, "/eboutic/")

    def test_submit_invalid_basket(self):
        self.client.login(username="subscriber", password="plop")
        max_id = Product.objects.aggregate(res=Max("id"))["res"]
        self.client.cookies[
            "basket_items"
        ] = f"""[
            {{"id": {max_id + 1}, "name": "", "quantity": 1, "unit_price": 28}}
        ]"""
        response = self.client.post(reverse("eboutic:command"))
        self.assertIn(
            'basket_items=""',
            self.client.cookies["basket_items"].OutputString(),
        )
        self.assertIn(
            "Path=/eboutic",
            self.client.cookies["basket_items"].OutputString(),
        )
        self.assertRedirects(response, "/eboutic/")

    def test_submit_basket_illegal_quantity(self):
        self.client.login(username="subscriber", password="plop")
        self.client.cookies[
            "basket_items"
        ] = """[
            {"id": 4, "name": "Barbar", "quantity": -1, "unit_price": 1.7}
        ]"""
        response = self.client.post(reverse("eboutic:command"))
        self.assertRedirects(response, "/eboutic/")

    def test_buy_subscribe_product_with_credit_card(self):
        self.client.login(username="old_subscriber", password="plop")
        response = self.client.get(
            reverse("core:user_profile", kwargs={"user_id": self.old_subscriber.id})
        )
        self.assertTrue("Non cotisant" in str(response.content))
        self.client.cookies[
            "basket_items"
        ] = """[
            {"id": 2, "name": "Cotis 2 semestres", "quantity": 1, "unit_price": 28}
        ]"""
        response = self.client.post(reverse("eboutic:command"))
        self.assertInHTML(
            "<tr><td>Cotis 2 semestres</td><td>1</td><td>28.00 €</td></tr>",
            response.content.decode(),
        )
        basket = Basket.objects.get(id=self.client.session["basket_id"])
        self.assertEqual(basket.items.count(), 1)
        response = self.generate_bank_valid_answer_from_page_content(response.content)
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.content.decode("utf-8") == "Payment successful")

        subscriber = User.objects.get(id=self.old_subscriber.id)
        self.assertEqual(subscriber.subscriptions.count(), 2)
        sub = subscriber.subscriptions.order_by("-subscription_end").first()
        self.assertTrue(sub.is_valid_now())
        self.assertEqual(sub.member, subscriber)
        self.assertEqual(sub.subscription_type, "deux-semestres")
        self.assertEqual(sub.location, "EBOUTIC")

    def test_buy_refill_product_with_credit_card(self):
        self.client.login(username="subscriber", password="plop")
        # basket contains 1 refill item worth 15€
        self.client.cookies["basket_items"] = json.dumps(
            [{"id": 3, "name": "Rechargement 15 €", "quantity": 1, "unit_price": 15}]
        )
        initial_balance = self.subscriber.customer.amount
        response = self.client.post(reverse("eboutic:command"))

        response = self.generate_bank_valid_answer_from_page_content(response.content)
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.content.decode() == "Payment successful")
        new_balance = Customer.objects.get(user=self.subscriber).amount
        self.assertEqual(new_balance, initial_balance + 15)

    def test_alter_basket_after_submission(self):
        self.client.login(username="subscriber", password="plop")
        self.client.cookies["basket_items"] = json.dumps(
            [{"id": 4, "name": "Barbar", "quantity": 1, "unit_price": 1.7}]
        )
        response = self.client.post(reverse("eboutic:command"))
        self.client.cookies["basket_items"] = json.dumps(
            [  # alter basket
                {"id": 4, "name": "Barbar", "quantity": 3, "unit_price": 1.7}
            ]
        )
        self.client.post(reverse("eboutic:command"))
        response = self.generate_bank_valid_answer_from_page_content(response.content)
        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Basket processing failed with error: SuspiciousOperation('Basket total and amount do not match'",
            response.content.decode("utf-8"),
        )

    def test_buy_simple_product_with_credit_card(self):
        self.client.login(username="subscriber", password="plop")
        self.client.cookies["basket_items"] = json.dumps(
            [{"id": 4, "name": "Barbar", "quantity": 1, "unit_price": 1.7}]
        )
        response = self.client.post(reverse("eboutic:command"))
        response = self.generate_bank_valid_answer_from_page_content(response.content)
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.content.decode("utf-8") == "Payment successful")

        selling = (
            Selling.objects.filter(customer=self.subscriber.customer)
            .order_by("-date")
            .first()
        )
        self.assertEqual(selling.payment_method, "CARD")
        self.assertEqual(selling.quantity, 1)
        self.assertEqual(selling.unit_price, self.barbar.selling_price)
        self.assertEqual(selling.counter.type, "EBOUTIC")
        self.assertEqual(selling.product, self.barbar)
