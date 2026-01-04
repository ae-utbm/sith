import json

import pytest
from django.test import Client
from model_bakery import baker

from counter.models import Counter, User


class TestCounterBulkRoutes:
    def setup_method(self):
        self.admin = baker.make(User, is_superuser=True)
        self.counter = baker.make(Counter)
        self.client = Client()
        self.client.force_login(self.admin)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "users_number,already_in_number,invalid_users_number,expected_code,invalid_counter",
        [
            (1, 0, 0, 200, False),
            (4, 0, 0, 200, False),
            (0, 1, 0, 200, False),
            (0, 4, 0, 200, False),
            (2, 2, 0, 200, False),
            (2, 2, 2, 200, False),
            (0, 0, 1, 200, False),
            (0, 0, 4, 200, False),
            (1, 0, 0, 404, True),
        ],
    )
    def test_counter_create_bulk(
        self,
        users_number,
        already_in_number,
        invalid_users_number,
        expected_code,
        invalid_counter,
    ):
        counter_id = 9999 if invalid_counter else self.counter.id

        user_id_list = []

        valid_users_id = []
        for _ in range(users_number):
            user = baker.make(User)
            user_id_list.append(user.id)
            valid_users_id.append(user.id)

        user_to_add = []
        for _ in range(already_in_number):
            user = baker.make(User)
            user_id_list.append(user.id)
            user_to_add.append(user)
            valid_users_id.append(user.id)
        self.counter.sellers.add(*user_to_add)

        for i in range(invalid_users_number):
            user_id_list.append(9999 + i) # noqa: PERF401

        response = self.client.put(
            f"/api/counter/{counter_id}/seller/add",
            content_type="application/json",
            data=json.dumps({"users_id": user_id_list}),
        )

        assert response.status_code == expected_code

        if response.status_code == 200:
            for user_id in valid_users_id:
                assert self.counter.sellers.filter(pk=user_id).exists()

            for i in range(invalid_users_number):
                assert not self.counter.sellers.filter(pk=9999 + i).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "users_number,already_in_number,invalid_users_number,expected_code,invalid_counter",
        [
            (1, 0, 0, 200, False),
            (4, 0, 0, 200, False),
            (0, 1, 0, 200, False),
            (0, 4, 0, 200, False),
            (2, 2, 0, 200, False),
            (2, 2, 2, 200, False),
            (0, 0, 1, 200, False),
            (0, 0, 4, 200, False),
            (1, 0, 0, 404, True),
        ],
    )
    def test_counter_remove_bulk(
        self,
        users_number,
        already_in_number,
        invalid_users_number,
        expected_code,
        invalid_counter,
    ):
        counter_id = 9999 if invalid_counter else self.counter.id

        user_id_list = []

        valid_user_ids = []

        for _ in range(users_number):
            user = baker.make(User)
            user_id_list.append(user.id)

        user_to_add = []
        for _ in range(already_in_number):
            user = baker.make(User)
            user_id_list.append(user.id)
            user_to_add.append(user)
        self.counter.sellers.add(*user_to_add)
        valid_user_ids.extend([u.id for u in user_to_add])

        for i in range(invalid_users_number):
            user_id_list.append(9999 + i) # noqa: PERF401

        users_to_add_all = []
        for uid in user_id_list:
            u = User.objects.filter(pk=uid).first()
            if u:
                users_to_add_all.append(u)
        self.counter.sellers.add(*users_to_add_all)

        response = self.client.delete(
            f"/api/counter/{counter_id}/seller/remove",
            data=json.dumps({"users_id": user_id_list}),
            content_type="application/json",
        )

        assert response.status_code == expected_code

        if response.status_code == 200:
            for user_id in user_id_list:
                assert not self.counter.sellers.filter(pk=user_id).exists()

            for i in range(invalid_users_number):
                assert not self.counter.sellers.filter(pk=9999 + i).exists()
