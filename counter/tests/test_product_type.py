import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from model_bakery import baker, seq
from ninja_extra.testing import TestClient

from core.baker_recipes import board_user, subscriber_user
from core.models import RealGroup, User
from counter.api import ProductTypeController
from counter.models import ProductType


@pytest.fixture
def product_types(db) -> list[ProductType]:
    """All existing product types, ordered by their `order` field"""
    # delete product types that have been created in the `populate` command
    ProductType.objects.all().delete()
    return baker.make(ProductType, _quantity=5, order=seq(0))


@pytest.mark.django_db
def test_fetch_product_types(product_types: list[ProductType]):
    """Test that the API returns the right products in the right order"""
    client = TestClient(ProductTypeController)
    response = client.get("")
    assert response.status_code == 200
    assert [i["id"] for i in response.json()] == [t.id for t in product_types]


@pytest.mark.django_db
def test_move_below_product_type(product_types: list[ProductType]):
    """Test that moving a product below another works"""
    client = TestClient(ProductTypeController)
    response = client.patch(
        f"/{product_types[-1].id}/move", query={"below": product_types[0].id}
    )
    assert response.status_code == 200
    new_order = [i["id"] for i in client.get("").json()]
    assert new_order == [
        product_types[0].id,
        product_types[-1].id,
        *[t.id for t in product_types[1:-1]],
    ]


@pytest.mark.django_db
def test_move_above_product_type(product_types: list[ProductType]):
    """Test that moving a product above another works"""
    client = TestClient(ProductTypeController)
    response = client.patch(
        f"/{product_types[1].id}/move", query={"above": product_types[0].id}
    )
    assert response.status_code == 200
    new_order = [i["id"] for i in client.get("").json()]
    assert new_order == [
        product_types[1].id,
        product_types[0].id,
        *[t.id for t in product_types[2:]],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_factory", "status_code"),
    [
        (lambda: baker.make(User, is_superuser=True), 200),
        (subscriber_user.make, 403),
        (board_user.make, 403),
        (
            lambda: baker.make(
                User,
                groups=[RealGroup.objects.get(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)],
            ),
            200,
        ),
        (
            lambda: baker.make(
                User,
                groups=[
                    RealGroup.objects.get(pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)
                ],
            ),
            200,
        ),
    ],
)
def test_controller_permissions(client: Client, user_factory, status_code):
    client.force_login(user_factory())
    response = client.get(reverse("api:fetch_product_types"))
    assert response.status_code == status_code
