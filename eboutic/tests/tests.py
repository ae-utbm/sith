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
import urllib
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.models import User
from counter.models import Counter, Customer, Product, Selling
from eboutic.models import Basket, BasketItem

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class TestEboutic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.barbar = Product.objects.get(code="BARB")
        cls.refill = Product.objects.get(code="15REFILL")
        cls.cotis = Product.objects.get(code="1SCOTIZ")
        cls.eboutic = Counter.objects.get(name="Eboutic")
        cls.skia = User.objects.get(username="skia")
        cls.subscriber = User.objects.get(username="subscriber")
        cls.old_subscriber = User.objects.get(username="old_subscriber")
        cls.public = User.objects.get(username="public")

    def get_busy_basket(self, user) -> Basket:
        """Create and return a basket with 3 barbar and 1 cotis in it.

        Edit the client session to store the basket id in it.
        """
        session = self.client.session
        basket = Basket.objects.create(user=user)
        session["basket_id"] = basket.id
        session.save()
        BasketItem.from_product(self.barbar, 3, basket).save()
        BasketItem.from_product(self.cotis, 1, basket).save()
        return basket

    def generate_bank_valid_answer(self) -> str:
        basket = Basket.from_session(self.client.session)
        basket_id = basket.id
        amount = int(basket.total * 100)
        query = f"Amount={amount}&BasketID={basket_id}&Auto=42&Error=00000"
        with open("./eboutic/tests/private_key.pem", "br") as f:
            PRIVKEY = f.read()
        with open("./eboutic/tests/public_key.pem") as f:
            settings.SITH_EBOUTIC_PUB_KEY = f.read()
        key: RSAPrivateKey = load_pem_private_key(PRIVKEY, None)
        sig = key.sign(query.encode("utf-8"), PKCS1v15(), SHA1())
        b64sig = base64.b64encode(sig).decode("ascii")

        url = reverse("eboutic:etransation_autoanswer") + "?%s&Sig=%s" % (
            query,
            urllib.parse.quote_plus(b64sig),
        )
        return url

    def test_buy_with_sith_account(self):
        self.client.force_login(self.subscriber)
        self.subscriber.customer.amount = 100  # give money before test
        self.subscriber.customer.save()
        basket = self.get_busy_basket(self.subscriber)
        amount = basket.total
        response = self.client.post(reverse("eboutic:pay_with_sith"))
        self.assertRedirects(response, "/eboutic/pay/success/")
        new_balance = Customer.objects.get(user=self.subscriber).amount
        assert float(new_balance) == 100 - amount
        expected = 'basket_items=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/eboutic'
        assert expected == self.client.cookies["basket_items"].OutputString()

    def test_buy_with_sith_account_no_money(self):
        self.client.force_login(self.subscriber)
        basket = self.get_busy_basket(self.subscriber)
        initial = basket.total - 1  # just not enough to complete the sale
        self.subscriber.customer.amount = initial
        self.subscriber.customer.save()
        response = self.client.post(reverse("eboutic:pay_with_sith"))
        self.assertRedirects(response, "/eboutic/pay/failure/")
        new_balance = Customer.objects.get(user=self.subscriber).amount
        assert float(new_balance) == initial
        # this cookie should be removed after payment
        expected = 'basket_items=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/eboutic'
        assert expected == self.client.cookies["basket_items"].OutputString()

    def test_buy_subscribe_product_with_credit_card(self):
        self.client.force_login(self.old_subscriber)
        response = self.client.get(
            reverse("core:user_profile", kwargs={"user_id": self.old_subscriber.id})
        )
        assert "Non cotisant" in str(response.content)
        self.client.cookies["basket_items"] = """[
            {"id": 2, "name": "Cotis 2 semestres", "quantity": 1, "unit_price": 28}
        ]"""
        response = self.client.get(reverse("eboutic:command"))
        self.assertInHTML(
            "<tr><td>Cotis 2 semestres</td><td>1</td><td>28.00 €</td></tr>",
            response.text,
        )
        basket = Basket.objects.get(id=self.client.session["basket_id"])
        assert basket.items.count() == 1
        response = self.client.get(self.generate_bank_valid_answer())
        assert response.status_code == 200
        assert response.content.decode("utf-8") == "Payment successful"

        subscriber = User.objects.get(id=self.old_subscriber.id)
        assert subscriber.subscriptions.count() == 2
        sub = subscriber.subscriptions.order_by("-subscription_end").first()
        assert sub.is_valid_now()
        assert sub.member == subscriber
        assert sub.subscription_type == "deux-semestres"
        assert sub.location == "EBOUTIC"

    def test_buy_refill_product_with_credit_card(self):
        self.client.force_login(self.subscriber)
        # basket contains 1 refill item worth 15€
        self.client.cookies["basket_items"] = json.dumps(
            [{"id": 3, "name": "Rechargement 15 €", "quantity": 1, "unit_price": 15}]
        )
        initial_balance = self.subscriber.customer.amount
        self.client.get(reverse("eboutic:command"))

        url = self.generate_bank_valid_answer()
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.text == "Payment successful"
        new_balance = Customer.objects.get(user=self.subscriber).amount
        assert new_balance == initial_balance + 15

    def test_alter_basket_after_submission(self):
        self.client.force_login(self.subscriber)
        self.client.cookies["basket_items"] = json.dumps(
            [{"id": 4, "name": "Barbar", "quantity": 1, "unit_price": 1.7}]
        )
        self.client.get(reverse("eboutic:command"))
        et_answer_url = self.generate_bank_valid_answer()
        self.client.cookies["basket_items"] = json.dumps(
            [  # alter basket
                {"id": 4, "name": "Barbar", "quantity": 3, "unit_price": 1.7}
            ]
        )
        self.client.get(reverse("eboutic:command"))
        response = self.client.get(et_answer_url)
        assert response.status_code == 500
        msg = (
            "Basket processing failed with error: "
            "SuspiciousOperation('Basket total and amount do not match'"
        )
        assert msg in response.content.decode("utf-8")

    def test_buy_simple_product_with_credit_card(self):
        self.client.force_login(self.subscriber)
        self.client.cookies["basket_items"] = json.dumps(
            [{"id": 4, "name": "Barbar", "quantity": 1, "unit_price": 1.7}]
        )
        self.client.get(reverse("eboutic:command"))
        et_answer_url = self.generate_bank_valid_answer()
        response = self.client.get(et_answer_url)
        assert response.status_code == 200
        assert response.content.decode("utf-8") == "Payment successful"

        selling = (
            Selling.objects.filter(customer=self.subscriber.customer)
            .order_by("-date")
            .first()
        )
        assert selling.payment_method == "CARD"
        assert selling.quantity == 1
        assert selling.unit_price == self.barbar.selling_price
        assert selling.counter.type == "EBOUTIC"
        assert selling.product == self.barbar
