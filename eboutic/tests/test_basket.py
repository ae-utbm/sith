from datetime import datetime, timezone

import pytest
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.baker_recipes import subscriber_user
from core.models import Group, User
from counter.baker_recipes import product_recipe, refill_recipe, sale_recipe
from counter.models import (
    Counter,
    Customer,
    ProductType,
    get_eboutic,
)
from counter.tests.test_counter import BasketItem
from eboutic.models import Basket


@pytest.mark.django_db
def test_get_eboutic():
    assert Counter.objects.get(name="Eboutic") == get_eboutic()

    baker.make(Counter, type="EBOUTIC")

    assert Counter.objects.get(name="Eboutic") == get_eboutic()


@pytest.mark.django_db
def test_eboutic_access_unregistered(client: Client):
    eboutic_url = reverse("eboutic:main")
    assertRedirects(
        client.get(eboutic_url), reverse("core:login", query={"next": eboutic_url})
    )


@pytest.mark.django_db
def test_eboutic_access_new_customer(client: Client):
    user = baker.make(User)
    assert not Customer.objects.filter(user=user).exists()

    client.force_login(user)

    assert client.get(reverse("eboutic:main")).status_code == 200
    assert Customer.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_eboutic_access_old_customer(client: Client):
    user = baker.make(User)
    customer = Customer.get_or_create(user)[0]

    client.force_login(user)

    assert client.get(reverse("eboutic:main")).status_code == 200
    assert Customer.objects.filter(user=user).first() == customer


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("sellings", "refillings", "expected"),
    (
        ([], [], None),
        (
            [datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc)],
            [],
            datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            [],
            [datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc)],
            datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            [datetime(2025, 2, 7, 1, 2, 3, tzinfo=timezone.utc)],
            [datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc)],
            datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            [datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc)],
            [datetime(2025, 2, 7, 1, 2, 3, tzinfo=timezone.utc)],
            datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            [
                datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc),
                datetime(2025, 2, 7, 1, 2, 3, tzinfo=timezone.utc),
            ],
            [datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc)],
            datetime(2025, 3, 7, 1, 2, 3, tzinfo=timezone.utc),
        ),
    ),
)
def test_eboutic_basket_expiry(
    client: Client,
    sellings: list[datetime],
    refillings: list[datetime],
    expected: datetime | None,
):
    eboutic = get_eboutic()

    customer = baker.make(Customer)

    client.force_login(customer.user)

    if sellings:
        sale_recipe.make(
            customer=customer,
            counter=eboutic,
            date=iter(sellings),
            _quantity=len(sellings),
            _bulk_create=True,
        )
    if refillings:
        refill_recipe.make(
            customer=customer,
            counter=eboutic,
            date=iter(refillings),
            _quantity=len(refillings),
            _bulk_create=True,
        )

    assert (
        f'x-data="basket({int(expected.timestamp() * 1000) if expected else "null"})"'
        in client.get(reverse("eboutic:main")).text
    )


class TestEboutic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group_cotiz = baker.make(Group)
        cls.group_public = baker.make(Group)

        cls.new_customer = baker.make(User)
        cls.new_customer_adult = baker.make(User)
        cls.subscriber = subscriber_user.make()

        cls.set_age(cls.new_customer, 5)
        cls.set_age(cls.new_customer_adult, 20)
        cls.set_age(cls.subscriber, 20)

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
        cls.not_in_counter = product_recipe.make(
            selling_price=3.5, product_type=product_type
        )
        cls.cotiz = product_recipe.make(selling_price=10, product_type=product_type)

        cls.group_public.products.add(cls.snack, cls.beer, cls.not_in_counter)
        cls.group_cotiz.products.add(cls.cotiz)

        cls.subscriber.groups.add(cls.group_cotiz, cls.group_public)
        cls.new_customer.groups.add(cls.group_public)
        cls.new_customer_adult.groups.add(cls.group_public)

        cls.eboutic = get_eboutic()
        cls.eboutic.products.add(cls.cotiz, cls.beer, cls.snack)

    @classmethod
    def set_age(cls, user: User, age: int):
        user.date_of_birth = localdate().replace(year=localdate().year - age)
        user.save()

    def submit_basket(
        self, basket: list[BasketItem], client: Client | None = None
    ) -> HttpResponse:
        used_client: Client = client if client is not None else self.client
        data = {
            "form-TOTAL_FORMS": str(len(basket)),
            "form-INITIAL_FORMS": "0",
        }
        for index, item in enumerate(basket):
            data.update(item.to_form(index))
        return used_client.post(reverse("eboutic:main"), data)

    def test_submit_empty_basket(self):
        self.client.force_login(self.subscriber)
        for basket in [
            [],
            [BasketItem(None, None)],
            [BasketItem(None, None), BasketItem(None, None)],
        ]:
            response = self.submit_basket(basket)
            assert response.status_code == 200
            assert "Votre panier est vide" in response.text

    def test_submit_invalid_basket(self):
        self.client.force_login(self.subscriber)
        for item in [
            BasketItem(-1, 2),
            BasketItem(self.snack.id, -1),
            BasketItem(None, 1),
            BasketItem(self.snack.id, None),
        ]:
            response = self.submit_basket([item])
            assert response.status_code == 200

    def test_anonymous(self):
        assertRedirects(
            self.client.get(reverse("eboutic:main")),
            reverse("core:login", query={"next": reverse("eboutic:main")}),
        )
        assertRedirects(
            self.submit_basket([]),
            reverse("core:login", query={"next": reverse("eboutic:main")}),
        )
        assertRedirects(
            self.submit_basket([BasketItem(self.snack.id, 1)]),
            reverse("core:login", query={"next": reverse("eboutic:main")}),
        )

    def test_add_forbidden_product(self):
        self.client.force_login(self.new_customer)
        response = self.submit_basket([BasketItem(self.beer.id, 1)])
        assert response.status_code == 200
        assert Basket.objects.first() is None

        response = self.submit_basket([BasketItem(self.cotiz.id, 1)])
        assert response.status_code == 200
        assert Basket.objects.first() is None

        response = self.submit_basket([BasketItem(self.not_in_counter.id, 1)])
        assert response.status_code == 200
        assert Basket.objects.first() is None

        self.client.force_login(self.new_customer)
        response = self.submit_basket([BasketItem(self.cotiz.id, 1)])
        assert response.status_code == 200
        assert Basket.objects.first() is None

        response = self.submit_basket([BasketItem(self.not_in_counter.id, 1)])
        assert response.status_code == 200
        assert Basket.objects.first() is None

    def test_create_basket(self):
        self.client.force_login(self.new_customer)
        assertRedirects(
            self.submit_basket([BasketItem(self.snack.id, 2)]),
            reverse("eboutic:checkout", kwargs={"basket_id": 1}),
        )
        assert Basket.objects.get(id=1).total == self.snack.selling_price * 2

        self.client.force_login(self.new_customer_adult)
        assertRedirects(
            self.submit_basket(
                [BasketItem(self.snack.id, 2), BasketItem(self.beer.id, 1)]
            ),
            reverse("eboutic:checkout", kwargs={"basket_id": 2}),
        )
        assert (
            Basket.objects.get(id=2).total
            == self.snack.selling_price * 2 + self.beer.selling_price
        )

        self.client.force_login(self.subscriber)
        assertRedirects(
            self.submit_basket(
                [
                    BasketItem(self.snack.id, 2),
                    BasketItem(self.beer.id, 1),
                    BasketItem(self.cotiz.id, 1),
                ]
            ),
            reverse("eboutic:checkout", kwargs={"basket_id": 3}),
        )
        assert (
            Basket.objects.get(id=3).total
            == self.snack.selling_price * 2
            + self.beer.selling_price
            + self.cotiz.selling_price
        )
