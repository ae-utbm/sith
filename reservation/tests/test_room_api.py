import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertNumQueries

from core.models import User
from reservation.models import Room


@pytest.mark.django_db
class TestFetchRoom:
    @pytest.fixture
    def user(self):
        return baker.make(
            User,
            user_permissions=[Permission.objects.get(codename="view_room")],
        )

    def test_fetch_simple(self, client: Client, user: User):
        rooms = baker.make(Room, _quantity=3, _bulk_create=True)
        client.force_login(user)
        response = client.get(reverse("api:fetch_reservable_rooms"))
        assert response.status_code == 200
        assert response.json() == [
            {
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "location": room.location,
                "club": {"id": room.club.id, "name": room.club.name},
            }
            for room in rooms
        ]

    def test_nb_queries(self, client: Client, user: User):
        client.force_login(user)
        with assertNumQueries(5):
            # 4 for authentication
            # 1 to fetch the actual data
            client.get(reverse("api:fetch_reservable_rooms"))
