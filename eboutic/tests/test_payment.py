from decimal import Decimal

from django.contrib.messages import get_messages
from django.contrib.messages.constants import DEFAULT_LEVELS
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.baker_recipes import subscriber_user
from counter.baker_recipes import product_recipe
from counter.models import Product, ProductType
from counter.tests.test_counter import force_refill_user
from eboutic.models import Basket, BasketItem


class TestPaymentBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = subscriber_user.make()
        cls.basket = baker.make(Basket, user=cls.customer)
        cls.refilling = Product.objects.get(code="15REFILL")

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
        assert (
            self.client.post(
                reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id}),
            ).status_code
            == 403
        )
        assert Basket.objects.filter(id=self.basket.id).first() is not None

    def test_unauthorized(self):
        self.client.force_login(subscriber_user.make())
        assert (
            self.client.post(
                reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id}),
            ).status_code
            == 403
        )
        assert Basket.objects.filter(id=self.basket.id).first() is not None

    def test_not_found(self):
        self.client.force_login(self.customer)
        assert (
            self.client.post(
                reverse(
                    "eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id + 1}
                ),
            ).status_code
            == 404
        )
        assert Basket.objects.filter(id=self.basket.id).first() is not None

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
        assert self.customer.customer.amount == Decimal("1")

    def test_not_enough_money(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id}),
        )
        assertRedirects(
            response,
            reverse("eboutic:payment_result", kwargs={"result": "failure"}),
        )

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert messages[0].level == DEFAULT_LEVELS["ERROR"]
        assert messages[0].message == "Solde insuffisant"

        assert Basket.objects.filter(id=self.basket.id).first() is not None

    def test_refilling_in_basket(self):
        BasketItem.from_product(self.refilling, 1, self.basket).save()
        self.client.force_login(self.customer)
        force_refill_user(self.customer, self.basket.total)
        response = self.client.post(
            reverse("eboutic:pay_with_sith", kwargs={"basket_id": self.basket.id}),
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
        assert self.customer.customer.amount == self.basket.total
