import base64
import urllib
from decimal import Decimal
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.contrib.messages import get_messages
from django.contrib.messages.constants import DEFAULT_LEVELS
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.baker_recipes import old_subscriber_user, subscriber_user
from counter.baker_recipes import product_recipe
from counter.models import Product, ProductType, Selling
from counter.tests.test_counter import force_refill_user
from eboutic.models import Basket, BasketItem

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class TestPaymentBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = subscriber_user.make()
        cls.basket = baker.make(Basket, user=cls.customer)
        cls.refilling = product_recipe.make(
            product_type_id=settings.SITH_COUNTER_PRODUCTTYPE_REFILLING,
            selling_price=15,
        )

        product_type = baker.make(ProductType)

        cls.snack = product_recipe.make(
            selling_price=1.5, special_selling_price=1, product_type=product_type
        )
        cls.beer = product_recipe.make(
            limit_age=18,
            selling_price=2.5,
            special_selling_price=1,
            product_type=product_type,
        )

        BasketItem.from_product(cls.snack, 1, cls.basket).save()
        BasketItem.from_product(cls.beer, 2, cls.basket).save()


class TestPaymentSith(TestPaymentBase):
    def test_anonymous(self):
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id})
        )
        assert response.status_code == 403
        assert Basket.objects.contains(self.basket), (
            "After an unsuccessful request, the basket should be kept"
        )

    def test_unauthorized(self):
        self.client.force_login(subscriber_user.make())
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id})
        )
        assert response.status_code == 403
        assert Basket.objects.contains(self.basket), (
            "After an unsuccessful request, the basket should be kept"
        )

    def test_not_found(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id + 1})
        )
        assert response.status_code == 404
        assert Basket.objects.contains(self.basket), (
            "After an unsuccessful request, the basket should be kept"
        )

    def test_only_post_allowed(self):
        self.client.force_login(self.customer)
        force_refill_user(self.customer, self.basket.total + 1)
        response = self.client.get(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id})
        )

        assert response.status_code == 405

        assert Basket.objects.contains(self.basket), (
            "After an unsuccessful request, the basket should be kept"
        )

        self.customer.customer.refresh_from_db()
        assert self.customer.customer.amount == self.basket.total + 1

    def test_buy_success(self):
        self.client.force_login(self.customer)
        force_refill_user(self.customer, self.basket.total + 1)
        assertRedirects(
            self.client.post(
                reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id}),
            ),
            reverse("eboutic:payment_result", kwargs={"result": "success"}),
        )
        assert Basket.objects.filter(id=self.basket.id).first() is None
        self.customer.customer.refresh_from_db()
        assert self.customer.customer.amount == Decimal(1)

        sellings = Selling.objects.filter(customer=self.customer.customer).order_by(
            "quantity"
        )
        assert len(sellings) == 2
        assert sellings[0].payment_method == Selling.PaymentMethod.SITH_ACCOUNT
        assert sellings[0].quantity == 1
        assert sellings[0].unit_price == self.snack.selling_price
        assert sellings[0].counter.type == "EBOUTIC"
        assert sellings[0].product == self.snack

        assert sellings[1].payment_method == Selling.PaymentMethod.SITH_ACCOUNT
        assert sellings[1].quantity == 2
        assert sellings[1].unit_price == self.beer.selling_price
        assert sellings[1].counter.type == "EBOUTIC"
        assert sellings[1].product == self.beer

    def test_not_enough_money(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id})
        )
        assertRedirects(
            response,
            reverse("eboutic:payment_result", kwargs={"result": "failure"}),
        )

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert messages[0].level == DEFAULT_LEVELS["ERROR"]
        assert messages[0].message == "Solde insuffisant"

        assert Basket.objects.contains(self.basket), (
            "After an unsuccessful request, the basket should be kept"
        )

    def test_refilling_in_basket(self):
        BasketItem.from_product(self.refilling, 1, self.basket).save()
        self.client.force_login(self.customer)
        force_refill_user(self.customer, self.basket.total + 1)
        self.customer.customer.refresh_from_db()
        initial_account_balance = self.customer.customer.amount
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id})
        )
        assertRedirects(
            response,
            reverse("eboutic:payment_result", kwargs={"result": "failure"}),
        )
        assert Basket.objects.filter(id=self.basket.id).first() is not None
        messages = list(get_messages(response.wsgi_request))
        assert messages[0].level == DEFAULT_LEVELS["ERROR"]
        assert (
            messages[0].message
            == "Vous ne pouvez pas acheter un rechargement avec de l'argent du sith"
        )
        self.customer.customer.refresh_from_db()
        assert self.customer.customer.amount == initial_account_balance


class TestPaymentCard(TestPaymentBase):
    def generate_bank_valid_answer(self, basket: Basket):
        query = (
            f"Amount={int(basket.total * 100)}&BasketID={basket.id}&Auto=42&Error=00000"
        )
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

    def test_buy_success(self):
        response = self.client.get(self.generate_bank_valid_answer(self.basket))
        assert response.status_code == 200
        assert response.content.decode("utf-8") == "Payment successful"
        assert Basket.objects.filter(id=self.basket.id).first() is None

        sellings = Selling.objects.filter(customer=self.customer.customer).order_by(
            "quantity"
        )
        assert len(sellings) == 2
        assert sellings[0].payment_method == Selling.PaymentMethod.CARD
        assert sellings[0].quantity == 1
        assert sellings[0].unit_price == self.snack.selling_price
        assert sellings[0].counter.type == "EBOUTIC"
        assert sellings[0].product == self.snack

        assert sellings[1].payment_method == Selling.PaymentMethod.CARD
        assert sellings[1].quantity == 2
        assert sellings[1].unit_price == self.beer.selling_price
        assert sellings[1].counter.type == "EBOUTIC"
        assert sellings[1].product == self.beer

    def test_buy_subscribe_product(self):
        customer = old_subscriber_user.make()
        assert customer.subscriptions.count() == 1
        assert not customer.subscriptions.first().is_valid_now()

        basket = baker.make(Basket, user=customer)
        BasketItem.from_product(Product.objects.get(code="2SCOTIZ"), 1, basket).save()
        response = self.client.get(self.generate_bank_valid_answer(basket))
        assert response.status_code == 200

        assert customer.subscriptions.count() == 2

        subscription = customer.subscriptions.order_by("-subscription_end").first()
        assert subscription.is_valid_now()
        assert subscription.subscription_type == "deux-semestres"
        assert subscription.location == "EBOUTIC"

    def test_buy_refilling(self):
        BasketItem.from_product(self.refilling, 2, self.basket).save()
        response = self.client.get(self.generate_bank_valid_answer(self.basket))
        assert response.status_code == 200

        self.customer.customer.refresh_from_db()
        assert self.customer.customer.amount == self.refilling.selling_price * 2

    def test_multiple_responses(self):
        bank_response = self.generate_bank_valid_answer(self.basket)

        response = self.client.get(bank_response)
        assert response.status_code == 200

        response = self.client.get(bank_response)
        assert response.status_code == 500
        assert (
            response.text
            == "Basket processing failed with error: SuspiciousOperation('Basket does not exists')"
        )

    def test_unknown_basket(self):
        bank_response = self.generate_bank_valid_answer(self.basket)
        self.basket.delete()
        response = self.client.get(bank_response)
        assert response.status_code == 500
        assert (
            response.text
            == "Basket processing failed with error: SuspiciousOperation('Basket does not exists')"
        )

    def test_altered_basket(self):
        bank_response = self.generate_bank_valid_answer(self.basket)
        BasketItem.from_product(self.snack, 1, self.basket).save()
        response = self.client.get(bank_response)
        assert response.status_code == 500
        assert (
            response.text == "Basket processing failed with error: "
            "SuspiciousOperation('Basket total and amount do not match')"
        )
