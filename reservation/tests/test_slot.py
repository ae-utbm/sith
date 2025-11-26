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
        perm = Permission.objects.get(codename="view_reservationslot")
        return baker.make(User, user_permissions=[perm])

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
class TestUpdateReservationSlotApi:
    @pytest.fixture
    def user(self):
        perm = Permission.objects.get(codename="change_reservationslot")
        return baker.make(User, user_permissions=[perm])

    @pytest.fixture
    def slot(self):
        return baker.make(
            ReservationSlot,
            start_at=now() + timedelta(hours=2),
            end_at=now() + timedelta(hours=4),
        )

    def test_ok(self, client: Client, user: User, slot: ReservationSlot):
        client.force_login(user)
        new_start = (slot.start_at + timedelta(hours=1)).replace(microsecond=0)
        response = client.patch(
            reverse("api:change_reservation_slot", kwargs={"slot_id": slot.id}),
            {"start_at": new_start, "end_at": new_start + timedelta(hours=2)},
            content_type="application/json",
        )
        assert response.status_code == 200
        slot.refresh_from_db()
        assert slot.start_at.replace(microsecond=0) == new_start
        assert slot.end_at.replace(microsecond=0) == new_start + timedelta(hours=2)

    def test_change_past_event(self, client, user: User, slot: ReservationSlot):
        """Test that moving a slot that already began is impossible."""
        client.force_login(user)
        new_start = now() - timedelta(hours=1)
        response = client.patch(
            reverse("api:change_reservation_slot", kwargs={"slot_id": slot.id}),
            {"start_at": new_start, "end_at": new_start + timedelta(hours=2)},
            content_type="application/json",
        )

        assert response.status_code == 422

    def test_move_event_to_occupied_slot(
        self, client: Client, user: User, slot: ReservationSlot
    ):
        client.force_login(user)
        other_slot = baker.make(
            ReservationSlot,
            room=slot.room,
            start_at=slot.end_at + timedelta(hours=1),
            end_at=slot.end_at + timedelta(hours=3),
        )
        response = client.patch(
            reverse("api:change_reservation_slot", kwargs={"slot_id": slot.id}),
            {
                "start_at": other_slot.start_at - timedelta(hours=1),
                "end_at": other_slot.start_at + timedelta(hours=1),
            },
            content_type="application/json",
        )
        assert response.status_code == 409


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


@pytest.mark.django_db
class TestCreateReservationSlot:
    @pytest.fixture
    def user(self):
        perms = Permission.objects.filter(
            codename__in=["add_reservationslot", "view_reservationslot"]
        )
        return baker.make(User, user_permissions=list(perms))

    def test_ok(self, client: Client, user: User):
        client.force_login(user)
        start = now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        room = baker.make(Room)
        response = client.post(
            reverse("reservation:make_reservation"),
            {"room": room.id, "start_at": start, "end_at": end},
        )
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect", "") == reverse("reservation:main")
        slot = ReservationSlot.objects.filter(room=room).last()
        assert slot is not None
        assert slot.start_at == start
        assert slot.end_at == end
        assert slot.author == user

    def test_permissions_denied(self, client: Client):
        client.force_login(baker.make(User))
        start = now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        response = client.post(
            reverse("reservation:make_reservation"),
            {"room": baker.make(Room), "start_at": start, "end_at": end},
        )
        assert response.status_code == 403
