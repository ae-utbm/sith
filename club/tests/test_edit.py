import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.models import Club, Membership
from core.baker_recipes import subscriber_user


@pytest.mark.django_db
def test_club_board_member_cannot_edit_club_properties(client: Client):
    user = subscriber_user.make()
    club = baker.make(Club, name="old name", is_active=True, address="old address")
    baker.make(Membership, club=club, user=user, role=7)
    client.force_login(user)
    res = client.post(
        reverse("club:club_edit", kwargs={"club_id": club.id}),
        {"name": "new name", "is_active": False, "address": "new address"},
    )
    # The request should success,
    # but admin-only fields shouldn't be taken into account
    assertRedirects(res, club.get_absolute_url())
    club.refresh_from_db()
    assert club.name == "old name"
    assert club.is_active
    assert club.address == "new address"


@pytest.mark.django_db
def test_edit_club_page_doesnt_crash(client: Client):
    """crash test for club:club_edit"""
    club = baker.make(Club)
    user = subscriber_user.make()
    baker.make(Membership, club=club, user=user, role=3)
    client.force_login(user)
    res = client.get(reverse("club:club_edit", kwargs={"club_id": club.id}))
    assert res.status_code == 200
