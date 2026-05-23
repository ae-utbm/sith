import pytest
from django.contrib.admin import AdminSite
from django.http import HttpRequest
from model_bakery import baker
from pytest_django.asserts import assertNumQueries

from api.admin import ApiClientAdmin
from api.models import ApiClient


@pytest.mark.django_db
def test_reset_hmac_action():
    client_admin = ApiClientAdmin(ApiClient, AdminSite())
    api_clients = baker.make(ApiClient, _quantity=4, _bulk_create=True)
    old_hmac_keys = [c.hmac_key for c in api_clients]
    with assertNumQueries(2):
        qs = ApiClient.objects.filter(id__in=[c.id for c in api_clients[2:4]])
        client_admin.reset_hmac_key(HttpRequest(), qs)
    for c in api_clients:
        c.refresh_from_db()
    assert api_clients[0].hmac_key == old_hmac_keys[0]
    assert api_clients[1].hmac_key == old_hmac_keys[1]
    assert api_clients[2].hmac_key != old_hmac_keys[2]
    assert api_clients[3].hmac_key != old_hmac_keys[3]
