from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from model_bakery import baker

from api.hashers import generate_key
from api.models import ApiClient, ApiKey
from api.schemas import ApiClientSchema

if TYPE_CHECKING:
    from django.test import Client


@pytest.mark.django_db
def test_api_client_controller(client: Client):
    key, hashed = generate_key()
    api_client = baker.make(ApiClient)
    baker.make(ApiKey, client=api_client, hashed_key=hashed)
    res = client.get(reverse("api:api-client-infos"), headers={"X-APIKey": key})
    assert res.status_code == 200
    assert res.json() == ApiClientSchema.from_orm(api_client).model_dump()
