import pytest
from django.test import Client
from django.urls import path
from model_bakery import baker
from ninja import NinjaAPI
from ninja.security import SessionAuth

from api.auth import ApiKeyAuth
from api.hashers import generate_key
from api.models import ApiClient, ApiKey

api = NinjaAPI()


@api.post("", auth=[ApiKeyAuth(), SessionAuth()])
def post_method(*args, **kwargs) -> None:
    """Dummy POST route authenticated by either api key or session cookie."""
    pass


urlpatterns = [path("", api.urls)]


@pytest.mark.django_db
@pytest.mark.urls(__name__)
@pytest.mark.parametrize("user_logged_in", [False, True])
def test_csrf_token(user_logged_in):
    """Test that CSRF check happens only when no api key is used."""
    client = Client(enforce_csrf_checks=True)
    key, hashed = generate_key()
    api_client = baker.make(ApiClient)
    baker.make(ApiKey, client=api_client, hashed_key=hashed)
    if user_logged_in:
        client.force_login(api_client.owner)

    response = client.post("")
    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF check Failed"

    # if using a valid API key, CSRF check should not occur
    response = client.post("", headers={"X-APIKey": key})
    assert response.status_code == 200

    # if using a wrong API key, ApiKeyAuth should fail,
    # leading to a fallback into SessionAuth and a CSRF check
    response = client.post("", headers={"X-APIKey": generate_key()[0]})
    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF check Failed"
