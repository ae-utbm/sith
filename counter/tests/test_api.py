import pytest
from django.contrib.auth.models import make_password
from django.test.client import Client
from django.urls import reverse
from model_bakery import baker

from core.baker_recipes import board_user, subscriber_user
from core.models import User
from counter.models import Counter


@pytest.fixture
def customer_user() -> User:
    return subscriber_user.make()


@pytest.fixture
def counter_bar() -> Counter:
    return baker.make(Counter, type="BAR")


@pytest.fixture
def barmen(counter_bar: Counter) -> User:
    user = subscriber_user.make(password=make_password("plop"))
    counter_bar.sellers.add(user)
    return user


@pytest.fixture
def board_member() -> User:
    return board_user.make()


@pytest.fixture
def root_user() -> User:
    return baker.make(User, is_superuser=True)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("connected_user"),
    [
        None,  # Anonymous user
        "barmen",
        "customer_user",
        "board_member",
        "root_user",
    ],
)
def test_get_customer_fail(
    client: Client,
    customer_user: User,
    request: pytest.FixtureRequest,
    connected_user: str | None,
):
    if connected_user is not None:
        client.force_login(request.getfixturevalue(connected_user))
    assert (
        client.get(
            reverse("api:get_customer", kwargs={"customer_id": customer_user.id})
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_get_customer_from_bar_fail_wrong_referrer(
    client: Client, customer_user: User, barmen: User, counter_bar: Counter
):
    client.post(
        reverse("counter:login", args=[counter_bar.pk]),
        {"username": barmen.username, "password": "plop"},
    )

    assert (
        client.get(
            reverse("api:get_customer", kwargs={"customer_id": customer_user.id})
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_get_customer_from_bar_success(
    client: Client, customer_user: User, barmen: User, counter_bar: Counter
):
    client.post(
        reverse("counter:login", args=[counter_bar.pk]),
        {"username": barmen.username, "password": "plop"},
    )

    response = client.get(
        reverse("api:get_customer", kwargs={"customer_id": customer_user.id}),
        HTTP_REFERER=reverse(
            "counter:click",
            kwargs={"counter_id": counter_bar.id, "user_id": customer_user.id},
        ),
    )
    assert response.status_code == 200
    assert response.json() == {
        "user": customer_user.id,
        "account_id": customer_user.customer.account_id,
        "amount": f"{customer_user.customer.amount:.2f}",
        "recorded_products": customer_user.customer.recorded_products,
    }
