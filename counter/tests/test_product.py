from io import BytesIO
from typing import Callable
from uuid import uuid4

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from PIL import Image
from pytest_django.asserts import assertNumQueries

from core.baker_recipes import board_user, subscriber_user
from core.models import Group, User
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
