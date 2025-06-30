from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker
from pytest_django.asserts import assertNumQueries

from core.models import User
from reservation.forms import ReservationForm
from reservation.models import ReservationSlot, Room


@pytest.mark.django_db
class TestFetchReservationSlotsApi:
    @pytest.fixture
    def user(self):
        return baker.make(
            User,
            user_permissions=[Permission.objects.get(codename="view_reservationslot")],
        )

    def test_fetch_simple(self, client: Client, user: User):
        slots = baker.make(ReservationSlot, _quantity=5, _bulk_create=True)
        client.force_login(user)
        response = client.get(reverse("api:fetch_reservation_slots"))
        assert response.json()["results"] == [
            {
                "id": slot.id,
                "room": slot.room_id,
                "comment": slot.comment,
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

    def test_nb_queries(self, client: Client, user: User):
        client.force_login(user)
        with assertNumQueries(5):
            # 4 for authentication
            # 1 to fetch the actual data
            client.get(reverse("api:fetch_reservation_slots"))


@pytest.mark.django_db
class TestReservationForm:
    def test_ok(self):
        start = now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        form = ReservationForm(
            author=baker.make(User),
            data={"room": baker.make(Room), "start_at": start, "end_at": end},
        )
        assert form.is_valid()

    @pytest.mark.parametrize(
        ("start_date", "end_date", "errors"),
        [
            (
                now() - timedelta(hours=2),
                now() + timedelta(hours=2),
                {"start_at": ["Assurez-vous que cet horodatage est dans le futur"]},
            ),
            (
                now() + timedelta(hours=3),
                now() + timedelta(hours=2),
                {"__all__": ["Le début doit être placé avant la fin"]},
            ),
        ],
    )
    def test_invalid_timedates(self, start_date, end_date, errors):
        form = ReservationForm(
            author=baker.make(User),
            data={"room": baker.make(Room), "start_at": start_date, "end_at": end_date},
        )
        assert not form.is_valid()
        assert form.errors == errors

    def test_unavailable_room(self):
        room = baker.make(Room)
        baker.make(
            ReservationSlot,
            room=room,
            start_at=now() + timedelta(hours=2),
            end_at=now() + timedelta(hours=4),
        )
        form = ReservationForm(
            author=baker.make(User),
            data={
                "room": room,
                "start_at": now() + timedelta(hours=1),
                "end_at": now() + timedelta(hours=3),
            },
        )
        assert not form.is_valid()
        assert form.errors == {
            "__all__": ["Il y a déjà une réservation sur ce créneau."]
        }
