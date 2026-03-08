from io import BytesIO
from typing import Callable
from uuid import uuid4

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe
from PIL import Image
from pytest_django.asserts import assertNumQueries, assertRedirects

from club.models import Club
from core.baker_recipes import board_user, subscriber_user
from core.models import Group, User
from counter.baker_recipes import product_recipe
from counter.forms import ProductForm, ProductPriceFormSet
from counter.models import Price, Product, ProductType


@pytest.mark.django_db
@pytest.mark.parametrize("model", [Product, ProductType])
def test_resize_product_icon(model):
    """Test that the product icon is resized when saved."""
    # Product and ProductType icons have a height of 70px
    # so this image should be resized to 50x70
    img = Image.new("RGB", (100, 140))
    content = BytesIO()
    img.save(content, format="JPEG")
    name = str(uuid4())

    product = baker.make(
        model,
        icon=SimpleUploadedFile(
            f"{name}.jpg", content.getvalue(), content_type="image/jpeg"
        ),
    )

    assert product.icon.width == 50
    assert product.icon.height == 70
    assert product.icon.name == f"products/{name}.webp"
    assert Image.open(product.icon).format == "WEBP"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_factory", "status_code"),
    [
        (lambda: baker.make(User, is_superuser=True), 200),
        (board_user.make, 403),
        (subscriber_user.make, 403),
        (
            lambda: baker.make(
                User,
                groups=[Group.objects.get(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)],
            ),
            200,
        ),
        (
            lambda: baker.make(
                User,
                groups=[Group.objects.get(pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)],
            ),
            200,
        ),
    ],
)
def test_fetch_product_access(
    client: Client, user_factory: Callable[[], User], status_code: int
):
    """Test that only authorized users can use the `GET /product` route."""
    client.force_login(user_factory())
    assert (
        client.get(reverse("api:search_products_detailed")).status_code == status_code
    )


@pytest.mark.django_db
def test_fetch_product_nb_queries(client: Client):
    client.force_login(baker.make(User, is_superuser=True))
    cache.clear()
    with assertNumQueries(6):
        # - 2 for authentication
        # - 1 for pagination
        # - 1 for the actual request
        # - 2 to prefetch the related prices and groups
        client.get(reverse("api:search_products_detailed"))


class TestCreateProduct(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product_type = baker.make(ProductType)
        cls.club = baker.make(Club)
        cls.counter_admin = baker.make(
            User, groups=[Group.objects.get(id=settings.SITH_GROUP_COUNTER_ADMIN_ID)]
        )
        cls.data = {
            "name": "foo",
            "description": "bar",
            "product_type": cls.product_type.id,
            "club": cls.club.id,
            "code": "FOO",
            "purchase_price": 1.0,
            "selling_price": 1.0,
            "special_selling_price": 1.0,
            "limit_age": 0,
            "price-TOTAL_FORMS": 0,
            "price-INITIAL_FORMS": 0,
            "action-TOTAL_FORMS": 0,
            "action-INITIAL_FORMS": 0,
        }

    def test_form_simple(self):
        form = ProductForm(data=self.data)
        assert form.is_valid()
        instance = form.save()
        assert instance.club == self.club
        assert instance.product_type == self.product_type
        assert instance.name == "foo"

    def test_view_simple(self):
        self.client.force_login(self.counter_admin)
        url = reverse("counter:new_product")
        response = self.client.get(url)
        assert response.status_code == 200
        response = self.client.post(url, data=self.data)
        assertRedirects(response, reverse("counter:product_list"))
        product = Product.objects.last()
        assert product.name == "foo"
        assert product.club == self.club
        assert product.product_type == self.product_type


class TestPriceFormSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = product_recipe.make()
        cls.counter_admin = baker.make(
            User, groups=[Group.objects.get(id=settings.SITH_GROUP_COUNTER_ADMIN_ID)]
        )
        cls.groups = baker.make(Group, _quantity=3)

    def test_add_price(self):
        data = {
            "prices-0-amount": 2,
            "prices-0-label": "foo",
            "prices-0-groups": [self.groups[0].id, self.groups[1].id],
            "prices-0-is_always_shown": True,
            "prices-1-amount": 1.5,
            "prices-1-label": "",
            "prices-1-groups": [self.groups[1].id, self.groups[2].id],
            "prices-1-is_always_shown": False,
            "prices-TOTAL_FORMS": 2,
            "prices-INITIAL_FORMS": 0,
        }
        form = ProductPriceFormSet(instance=self.product, data=data)
        assert form.is_valid()
        form.save()
        prices = list(self.product.prices.order_by("amount"))
        assert len(prices) == 2
        assert prices[0].amount == 1.5
        assert prices[0].label == ""
        assert prices[0].is_always_shown is False
        assert set(prices[0].groups.all()) == {self.groups[1], self.groups[2]}
        assert prices[1].amount == 2
        assert prices[1].label == "foo"
        assert prices[1].is_always_shown is True
        assert set(prices[1].groups.all()) == {self.groups[0], self.groups[1]}

    def test_change_prices(self):
        price_a = baker.make(
            Price, product=self.product, amount=1.5, groups=self.groups[:1]
        )
        price_b = baker.make(
            Price, product=self.product, amount=2, groups=self.groups[1:]
        )
        data = {
            "prices-0-id": price_a.id,
            "prices-0-DELETE": True,
            "prices-1-id": price_b.id,
            "prices-1-DELETE": False,
            "prices-1-amount": 3,
            "prices-1-label": "foo",
            "prices-1-groups": [self.groups[1].id],
            "prices-1-is_always_shown": True,
            "prices-TOTAL_FORMS": 2,
            "prices-INITIAL_FORMS": 2,
        }
        form = ProductPriceFormSet(instance=self.product, data=data)
        assert form.is_valid()
        form.save()
        prices = list(self.product.prices.order_by("amount"))
        assert len(prices) == 1
        assert prices[0].amount == 3
        assert prices[0].label == "foo"
        assert prices[0].is_always_shown is True
        assert set(prices[0].groups.all()) == {self.groups[1]}
        assert not Price.objects.filter(id=price_a.id).exists()


@pytest.mark.django_db
def test_price_for_user():
    groups = baker.make(Group, _quantity=4)
    users = [
        baker.make(User, groups=groups[:2]),
        baker.make(User, groups=groups[1:3]),
        baker.make(User, groups=[groups[3]]),
    ]
    recipe = Recipe(Price, product=product_recipe.make())
    prices = [
        recipe.make(amount=5, groups=groups, is_always_shown=True),
        recipe.make(amount=4, groups=[groups[0]], is_always_shown=True),
        recipe.make(amount=3, groups=[groups[1]], is_always_shown=False),
        recipe.make(amount=2, groups=[groups[3]], is_always_shown=False),
        recipe.make(amount=1, groups=[groups[1]], is_always_shown=False),
    ]
    qs = Price.objects.order_by("-amount")
    assert set(qs.for_user(users[0])) == {prices[0], prices[1], prices[4]}
    assert set(qs.for_user(users[1])) == {prices[0], prices[4]}
    assert set(qs.for_user(users[2])) == {prices[0], prices[3]}
