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
from PIL import Image
from pytest_django.asserts import assertNumQueries, assertRedirects

from club.models import Club
from core.baker_recipes import board_user, subscriber_user
from core.models import Group, User
from counter.forms import ProductForm
from counter.models import Product, ProductType


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
    with assertNumQueries(5):
        # - 2 for authentication
        # - 1 for pagination
        # - 1 for the actual request
        # - 1 to prefetch the related buying_groups
        client.get(reverse("api:search_products_detailed"))


class TestCreateProduct(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product_type = baker.make(ProductType)
        cls.club = baker.make(Club)
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
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
        }

    def test_form(self):
        form = ProductForm(data=self.data)
        assert form.is_valid()
        instance = form.save()
        assert instance.club == self.club
        assert instance.product_type == self.product_type
        assert instance.name == "foo"
        assert instance.selling_price == 1.0

    def test_view(self):
        self.client.force_login(
            baker.make(
                User,
                groups=[Group.objects.get(id=settings.SITH_GROUP_COUNTER_ADMIN_ID)],
            )
        )
        url = reverse("counter:new_product")
        response = self.client.get(url)
        assert response.status_code == 200
        response = self.client.post(url, data=self.data)
        assertRedirects(response, reverse("counter:product_list"))
        product = Product.objects.last()
        assert product.name == "foo"
        assert product.club == self.club
        assert product.product_type == self.product_type
