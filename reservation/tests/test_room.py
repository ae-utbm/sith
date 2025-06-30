import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertNumQueries, assertRedirects

from club.models import Club
from core.models import User
from reservation.forms import RoomUpdateForm
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


@pytest.mark.django_db
class TestCreateRoom:
    def test_ok(self, client: Client):
        perm = Permission.objects.get(codename="add_room")
        club = baker.make(Club)
        client.force_login(
            baker.make(User, user_permissions=[perm], groups=[club.board_group])
        )
        response = client.post(
            reverse("reservation:room_create"),
            data={"club": club.id, "name": "test", "location": "BELFORT"},
        )
        assertRedirects(response, reverse("club:tools", kwargs={"club_id": club.id}))
        room = Room.objects.last()
        assert room is not None
        assert room.club == club
        assert room.name == "test"
        assert room.location == "BELFORT"

    def test_permission_denied(self, client: Client):
        club = baker.make(Club)
        client.force_login(baker.make(User))
        response = client.get(reverse("reservation:room_create"))
        assert response.status_code == 403
        response = client.post(
            reverse("reservation:room_create"),
            data={"club": club.id, "name": "test", "location": "BELFORT"},
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestUpdateRoom:
    def test_ok(self, client: Client):
        club = baker.make(Club)
        room = baker.make(Room, club=club)
        client.force_login(baker.make(User, groups=[club.board_group]))
        url = reverse("reservation:room_edit", kwargs={"room_id": room.id})
        response = client.post(url, data={"name": "test", "location": "BELFORT"})
        assertRedirects(response, url)
        room.refresh_from_db()
        assert room.club == club
        assert room.name == "test"
        assert room.location == "BELFORT"

    def test_permission_denied(self, client: Client):
        club = baker.make(Club)
        room = baker.make(Room, club=club)
        client.force_login(baker.make(User))
        url = reverse("reservation:room_edit", kwargs={"room_id": room.id})
        response = client.get(url)
        assert response.status_code == 403
        response = client.post(url, data={"name": "test", "location": "BELFORT"})
        assert response.status_code == 403


@pytest.mark.django_db
class TestUpdateRoomForm:
    def test_form_club_edition_rights(self):
        """The club field should appear only if the request user can edit it."""
        room = baker.make(Room)
        perm = Permission.objects.get(codename="change_room")
        user_authorized = baker.make(User, user_permissions=[perm])
        assert "club" in RoomUpdateForm(request_user=user_authorized).fields

        user_forbidden = baker.make(User, groups=[room.club.board_group])
        assert "club" not in RoomUpdateForm(request_user=user_forbidden).fields
