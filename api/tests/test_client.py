import pytest
from django.contrib.auth.models import Permission
from django.test import TestCase
from model_bakery import baker

from api.models import ApiClient
from core.models import Group


class TestClientPermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = baker.make(ApiClient)
        cls.perms = baker.make(Permission, _quantity=10, _bulk_create=True)
        cls.api_client.groups.set(
            [
                baker.make(Group, permissions=cls.perms[0:3]),
                baker.make(Group, permissions=cls.perms[3:5]),
            ]
        )
        cls.api_client.client_permissions.set(
            [cls.perms[3], cls.perms[5], cls.perms[6], cls.perms[7]]
        )

    def test_all_permissions(self):
        assert self.api_client.all_permissions == {
            f"{p.content_type.app_label}.{p.codename}" for p in self.perms[0:8]
        }

    def test_has_perm(self):
        assert self.api_client.has_perm(
            f"{self.perms[1].content_type.app_label}.{self.perms[1].codename}"
        )
        assert not self.api_client.has_perm(
            f"{self.perms[9].content_type.app_label}.{self.perms[9].codename}"
        )

    def test_has_perms(self):
        assert self.api_client.has_perms(
            [
                f"{self.perms[1].content_type.app_label}.{self.perms[1].codename}",
                f"{self.perms[2].content_type.app_label}.{self.perms[2].codename}",
            ]
        )
        assert not self.api_client.has_perms(
            [
                f"{self.perms[1].content_type.app_label}.{self.perms[1].codename}",
                f"{self.perms[9].content_type.app_label}.{self.perms[9].codename}",
            ],
        )


@pytest.mark.django_db
def test_reset_hmac_key():
    client = baker.make(ApiClient)
    original_key = client.hmac_key
    client.reset_hmac(commit=True)
    assert len(client.hmac_key) == len(original_key)
    assert client.hmac_key != original_key
