import pytest
from model_bakery import baker
from django.test import Client
from counter.api import SellerCounterOrUserNotFoundErrorCode
from counter.models import Counter, User


class TestCounterBulkRoutes:
    def setup_method(self):
        self.admin = baker.make(User, is_superuser=True)
        self.user = baker.make(User)
        self.counter = baker.make(Counter)
        self.client = Client()
        # Add the base user as a seller of the counter
        self.counter.sellers.add(self.user)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "route,method,setup_users,post_ids,expected_status,expected_added,expected_removed,expected_not_existing,expected_code,expected_detail",
        [
            # Add a new seller
            ("add", "post", ["new"], lambda self: [self.new_seller.id], 200, lambda self: [self.new_seller.id], None, lambda self: [], None, None),
            # Add a non-existent seller
            ("add", "post", [], lambda self: [99999], 404, lambda self: [], None, lambda self: [99999], SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND, "No sellers were added. All user IDs not found."),
            # Add on a non-existent counter
            ("add", "post", [], lambda self: [self.user.id], 404, lambda self: [], None, lambda self: [self.user.id], SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND, "Counter does not exist."),
            # Add a seller already present
            ("add", "post", [], lambda self: [self.user.id], 200, lambda self: [self.user.id], None, lambda self: [], None, None),
            # Add multiple sellers (mixed)
            ("add", "post", ["new", "new2"], lambda self: [self.new_seller.id, self.new_seller2.id, 99999], 200, lambda self: [self.new_seller.id, self.new_seller2.id], None, lambda self: [99999], None, None),
            # No sellers added (all invalid)
            ("add", "post", [], lambda self: [99999, 88888], 404, lambda self: [], None, lambda self: [99999, 88888], SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND, None),
            # Remove an existing seller
            ("remove", "post", [], lambda self: [self.user.id], 200, None, lambda self: [self.user.id], lambda self: [], None, None),
            # Remove a non-existent seller
            ("remove", "post", [], lambda self: [99999], 404, None, lambda self: [], lambda self: [99999], SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND, None),
            # Remove on a non-existent counter
            ("remove", "post", [], lambda self: [self.user.id], 404, None, lambda self: [], lambda self: [self.user.id], SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND, None),
            # Remove a seller not present
            ("remove", "post", ["new"], lambda self: [self.new_seller.id], 404, None, lambda self: [], lambda self: [self.new_seller.id], SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND, None),
            # Remove multiple sellers (mixed)
            ("remove", "post", ["new", "new2"], lambda self: [self.user.id, self.new_seller.id, 99999], 200, None, lambda self: [self.user.id, self.new_seller.id], lambda self: [99999], None, None),
            # No sellers removed (all invalid)
            ("remove", "post", [], lambda self: [99999, 88888], 404, None, lambda self: [], lambda self: [99999, 88888], SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND, None),
        ]
    )
    def test_counter_bulk_routes(self, route, method, setup_users, post_ids, expected_status, expected_added, expected_removed, expected_not_existing, expected_code, expected_detail):
        self.client.force_login(self.admin)
        # Prepare additional users if needed
        if "new" in setup_users:
            self.new_seller = baker.make(User)
        if "new2" in setup_users:
            self.new_seller2 = baker.make(User)
        # Special case: for 'remove' with multiple sellers, add them as sellers
        if route == "remove" and "new" in setup_users and "new2" in setup_users:
            self.counter.sellers.add(self.new_seller)
            self.counter.sellers.add(self.new_seller2)
        # Build the URL
        if route == "add":
            url = f"/api/counter/{self.counter.id}/seller/add"
        else:
            url = f"/api/counter/{self.counter.id}/seller/remove"
        # Case: non-existent counter
        if expected_code == SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND:
            url = f"/api/counter/99999/seller/{route}"
        # Build the IDs to post
        ids = post_ids(self) if callable(post_ids) else post_ids
        # Resolve any nested lambdas for ids
        ids = [i(self) if callable(i) else i for i in ids]
        data = {"user_ids": ids}
        response = self.client.post(url, data, content_type="application/json")
        self.counter.refresh_from_db()
        assert response.status_code == expected_status
        json = response.json()
        if expected_status == 200:
            if expected_added is not None:
                added = expected_added(self) if callable(expected_added) else expected_added
                assert set(json["added_ids"]) == set(added)
            if expected_removed is not None:
                removed = expected_removed(self) if callable(expected_removed) else expected_removed
                assert set(json["removed_ids"]) == set(removed)
            if expected_not_existing is not None:
                not_existing = expected_not_existing(self) if callable(expected_not_existing) else expected_not_existing
                assert set(json["not_existing_ids"]) == set(not_existing)
        else:
            if expected_code:
                assert json["code"] == expected_code
            if expected_detail:
                assert json["detail"] == expected_detail
