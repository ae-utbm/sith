from unittest import mock
from unittest.mock import Mock

from django.db.models import Max
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from api.models import ApiClient, get_hmac_key
from core.baker_recipes import subscriber_user
from core.schemas import UserProfileSchema
from core.utils import hmac_hexdigest


def mocked_post(*, ok: bool):
    class MockedResponse(Mock):
        @property
        def ok(self):
            return ok

    def mocked():
        return MockedResponse()

    return mocked


class TestThirdPartyAuth(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = subscriber_user.make()
        cls.api_client = baker.make(ApiClient)

    def setUp(self):
        self.query = {
            "client_id": self.api_client.id,
            "third_party_app": "app",
            "privacy_link": "https://foobar.fr/",
            "username": "bibou",
            "callback_url": "https://callback.fr/",
        }
        self.query["signature"] = hmac_hexdigest(self.api_client.hmac_key, self.query)
        self.callback_data = {
            "user": UserProfileSchema.from_orm(self.user).model_dump()
        }
        self.callback_data["signature"] = hmac_hexdigest(
            self.api_client.hmac_key, self.callback_data["user"]
        )

    def test_auth_ok(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse("api-link:third-party-auth", query=self.query))
        assert res.status_code == 200
        with mock.patch("requests.post", new_callable=mocked_post(ok=True)) as mocked:
            res = self.client.post(
                reverse("api-link:third-party-auth"),
                data={"cgu_accepted": True, "is_username_valid": True, **self.query},
            )
            mocked.assert_called_once_with(
                self.query["callback_url"], data=self.callback_data
            )
        assertRedirects(
            res,
            reverse("api-link:third-party-auth-result", kwargs={"result": "success"}),
        )

    def test_callback_error(self):
        """Test that the user see the failure page if the callback request failed."""
        self.client.force_login(self.user)
        with mock.patch("requests.post", new_callable=mocked_post(ok=False)) as mocked:
            res = self.client.post(
                reverse("api-link:third-party-auth"),
                data={"cgu_accepted": True, "is_username_valid": True, **self.query},
            )
            mocked.assert_called_once_with(
                self.query["callback_url"], data=self.callback_data
            )
        assertRedirects(
            res,
            reverse("api-link:third-party-auth-result", kwargs={"result": "failure"}),
        )

    def test_wrong_signature(self):
        """Test that a 403 is raised if the signature of the query is wrong."""
        self.client.force_login(subscriber_user.make())
        new_key = get_hmac_key()
        del self.query["signature"]
        self.query["signature"] = hmac_hexdigest(new_key, self.query)
        res = self.client.get(reverse("api-link:third-party-auth", query=self.query))
        assert res.status_code == 403

    def test_cgu_not_accepted(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse("api-link:third-party-auth", query=self.query))
        assert res.status_code == 200
        res = self.client.post(reverse("api-link:third-party-auth"), data=self.query)
        assert res.status_code == 200  # no redirect means invalid form
        res = self.client.post(
            reverse("api-link:third-party-auth"),
            data={"cgu_accepted": False, "is_username_valid": False, **self.query},
        )
        assert res.status_code == 200

    def test_invalid_client(self):
        self.query["client_id"] = ApiClient.objects.aggregate(res=Max("id"))["res"] + 1
        res = self.client.get(reverse("api-link:third-party-auth", query=self.query))
        assert res.status_code == 403

    def test_missing_parameter(self):
        """Test that a 403 is raised if there is a missing parameter."""
        del self.query["username"]
        self.query["signature"] = hmac_hexdigest(self.api_client.hmac_key, self.query)
        res = self.client.get(reverse("api-link:third-party-auth", query=self.query))
        assert res.status_code == 403
