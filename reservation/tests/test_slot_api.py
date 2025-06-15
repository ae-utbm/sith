import pytest
from model_bakery import baker
from ninja_extra.testing import TestClient
from pytest_django.asserts import assertNumQueries

from reservation.api import ReservableRoomController, ReservationSlotController
from reservation.models import ReservationSlot


@pytest.mark.django_db
class TestFetchRoom:
    def test_fetch_simple(self):
        slots = baker.make(ReservationSlot, _quantity=5, _bulk_create=True)
        response = TestClient(ReservationSlotController).get("")
        assert response.json() == [
            {
                "id": slot.id,
                "room": slot.room_id,
                "comment": slot.comment,
                "nb_people": slot.nb_people,
                "start": slot.start_at.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                ),
                "end": slot.end_at.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                ),
                "author": {
                    "id": slot.author.id,
                    "first_name": slot.author.first_name,
                    "last_name": slot.author.last_name,
                    "nick_name": slot.author.nick_name,
                },
            }
            for slot in slots
        ]

    def test_nb_queries(self):
        with assertNumQueries(1):
            TestClient(ReservableRoomController).get("")
