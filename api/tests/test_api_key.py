import pytest
from django.test import RequestFactory
from model_bakery import baker

from api.auth import ApiKeyAuth
from api.hashers import generate_key
from api.models import ApiClient, ApiKey


@pytest.mark.django_db
def test_api_key_auth():
    key, hashed = generate_key()
    client = baker.make(ApiClient)
    baker.make(ApiKey, client=client, hashed_key=hashed)
    auth = ApiKeyAuth()

    assert auth.authenticate(RequestFactory().get(""), key) == client


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("key", "hashed"), [(generate_key()[0], generate_key()[1]), (generate_key()[0], "")]
)
def test_api_key_auth_invalid(key, hashed):
    client = baker.make(ApiClient)
    baker.make(ApiKey, client=client, hashed_key=hashed)
    auth = ApiKeyAuth()

    assert auth.authenticate(RequestFactory().get(""), key) is None
