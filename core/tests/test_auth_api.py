import json

import pytest
from django.contrib.auth.hashers import make_password
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from core.models import User
from core.schemas import UserSchema
from counter.models import Customer


def post_login(client: Client, identifier: str, password: str):
    return client.post(
        reverse("api:login"),
        data={"identifier": identifier, "password": password}
    )


@pytest.fixture()
def user(db) -> User:
    return baker.make(User, password=make_password("plop"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "identifier_getter",
    [
        lambda user: user.username,
        lambda user: user.email,
        lambda user: Customer.get_or_create(user)[0].account_id,
    ],
)
def test_api_login_success(client: Client, user: User, identifier_getter):
    response = post_login(client, identifier_getter(user), "plop")

    assert response.status_code == 200
    assert response.json() == UserSchema.model_validate(user).model_dump(mode="json")
    assert int(client.session["_auth_user_id"]) == user.id


@pytest.mark.django_db
def test_api_login_fail_invalid_credentials(client: Client, user: User):
    response = post_login(client, user.username, "wrong-password")

    assert response.status_code == 401
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_api_login_fail_if_already_authenticated(client: Client, user: User):
    already_logged_user = baker.make(User)
    client.force_login(already_logged_user)

    response = post_login(client, user.username, "plop")

    assert response.status_code == 403
    assert int(client.session["_auth_user_id"]) == already_logged_user.id
