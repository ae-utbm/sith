import pytest
from model_bakery import baker
from ninja_extra.testing import TestClient
from pytest_django.asserts import assertNumQueries

from reservation.api import ReservableRoomController
from reservation.models import Room


@pytest.mark.django_db
class TestFetchRoom:
    def test_fetch_simple(self):
        rooms = baker.make(Room, _quantity=3, _bulk_create=True)
        response = TestClient(ReservableRoomController).get("")
        assert response.json() == [
            {
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "address": room.address,
                "club": {"id": room.club.id, "name": room.club.name},
            }
            for room in rooms
        ]

    def test_nb_queries(self):
        with assertNumQueries(1):
            TestClient(ReservableRoomController).get("")
