# Copyright 2025 © AE UTBM
# See LICENSE file for details
import pytest
from model_bakery import baker
from django.test import Client

from counter.api import SellerCounterOrUserNotFoundErrorCode
from counter.models import Counter, User

@pytest.mark.django_db
class TestCounterAdminAPI:
    def setup_method(self):
        """Setup test data for each test."""
        self.client = Client()
        self.admin = baker.make(User, is_superuser=True)
        self.user = baker.make(User)
        self.counter = baker.make(Counter, name="Test Bar")
        self.counter.sellers.add(self.user)

    def test_add_seller_to_counter(self):
        """Admin can add a seller to a counter (new bulk route)."""
        self.client.force_login(self.admin)
        new_seller = baker.make(User)
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [new_seller.id]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 200
        assert new_seller in self.counter.sellers.all()
        assert response.json()["added_ids"] == [new_seller.id]
        assert response.json()["not_existing_ids"] == []

    def test_add_seller_to_counter_not_existing(self):
        """Admin tries to add a non-existing seller."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [99999]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND
        assert response.json()["detail"] == "No sellers were added. All user IDs not found."

    def test_add_seller_to_counter_counter_not_existing(self):
        """Admin tries to add a seller to a non-existing counter."""
        self.client.force_login(self.admin)
        url = f"/api/counter/99999/seller/add"
        data = {"user_ids": [self.user.id]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND
        assert response.json()["detail"] == "Counter does not exist."

    def test_remove_seller_from_counter(self):
        """Admin can remove a seller from a counter (new bulk route)."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [self.user.id]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 200
        assert self.user not in self.counter.sellers.all()
        assert response.json()["removed_ids"] == [self.user.id]
        assert response.json()["not_existing_ids"] == []

    def test_remove_seller_from_counter_not_existing(self):
        """Admin tries to remove a non-existing seller."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [99999]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND
        assert response.json()["detail"] == "No sellers were removed. All user IDs not found or not sellers."

    def test_remove_seller_from_counter_counter_not_existing(self):
        """Admin tries to remove a seller from a non-existing counter."""
        self.client.force_login(self.admin)
        url = f"/api/counter/99999/seller/remove"
        data = {"user_ids": [self.user.id]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND
        assert response.json()["detail"] == "Counter does not exist."

    def test_permission_denied_for_non_admin(self):
        """Non-admin user cannot manage sellers (bulk route)."""
        self.client.force_login(self.user)
        new_seller = baker.make(User)
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [new_seller.id]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 403
        assert "permission" in response.json().get("detail", "")

    def test_remove_nonexistent_seller(self):
        """Removing a seller who is not present should not fail (bulk route)."""
        self.client.force_login(self.admin)
        new_user = baker.make(User)
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [new_user.id]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 404
        assert new_user not in self.counter.sellers.all()
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND

    def test_add_existing_seller(self):
        """Adding a seller who is already present should succeed and not duplicate (bulk route)."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [self.user.id]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        sellers = list(self.counter.sellers.filter(id=self.user.id))
        assert response.status_code == 200
        assert len(sellers) == 1
        assert response.json()["added_ids"] == [self.user.id]

    def test_add_sellers_to_counter(self):
        """Admin can add multiple sellers to a counter."""
        self.client.force_login(self.admin)
        sellers = [baker.make(User) for _ in range(3)]
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [u.id for u in sellers]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 200
        assert set(response.json()["added_ids"]) == set(u.id for u in sellers)
        for u in sellers:
            assert u in self.counter.sellers.all()

    def test_add_sellers_to_counter_none_added(self):
        """Returns 404 if no sellers are added (all IDs invalid)."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [99999, 88888]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND

    def test_remove_sellers_from_counter(self):
        """Admin can remove multiple sellers from a counter."""
        self.client.force_login(self.admin)
        sellers = [baker.make(User) for _ in range(2)]
        for u in sellers:
            self.counter.sellers.add(u)
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [u.id for u in sellers]}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 200
        assert set(response.json()["removed_ids"]) == set(u.id for u in sellers)
        for u in sellers:
            assert u not in self.counter.sellers.all()

    def test_remove_sellers_from_counter_none_removed(self):
        """Returns 404 if no sellers are removed (all IDs invalid)."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [99999, 88888]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND

    def test_add_sellers_to_counter_mixed(self):
        """Admin adds several sellers, some existing, some non-existing."""
        self.client.force_login(self.admin)
        sellers = [baker.make(User) for _ in range(2)]
        non_existing_ids = [99999, 88888]
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [u.id for u in sellers] + non_existing_ids}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 200
        assert set(response.json()["added_ids"]) == set(u.id for u in sellers)
        assert set(response.json()["not_existing_ids"]) == set(non_existing_ids)
        for u in sellers:
            assert u in self.counter.sellers.all()

    def test_add_sellers_to_counter_all_inexistant(self):
        """Admin tries to add only non-existing sellers."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/add"
        data = {"user_ids": [99999, 88888]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND

    def test_remove_sellers_from_counter_mixed(self):
        """Admin removes several sellers, some existing, some non-existing."""
        self.client.force_login(self.admin)
        sellers = [baker.make(User) for _ in range(2)]
        for u in sellers:
            self.counter.sellers.add(u)
        non_existing_ids = [99999, 88888]
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [u.id for u in sellers] + non_existing_ids}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == 200
        assert set(response.json()["removed_ids"]) == set(u.id for u in sellers)
        assert set(response.json()["not_existing_ids"]) == set(non_existing_ids)
        for u in sellers:
            assert u not in self.counter.sellers.all()

    def test_remove_sellers_from_counter_all_inexistant(self):
        """Admin tries to remove only non-existing sellers."""
        self.client.force_login(self.admin)
        url = f"/api/counter/{self.counter.id}/seller/remove"
        data = {"user_ids": [99999, 88888]}
        response = self.client.post(url, data, content_type="application/json")
        assert response.status_code == 404
        assert response.json()["code"] == SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND
