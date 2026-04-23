from datetime import timedelta

import pytest
from django.conf import settings
from django.db import ProgrammingError
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from model_bakery.recipe import Recipe
from pytest_django.asserts import assertRedirects

from club.models import Club, ClubRole, Membership
from core.baker_recipes import subscriber_user
from core.models import User


@pytest.mark.django_db
def test_club_queryset_having_board_member():
    clubs = baker.make(Club, _quantity=5)
    user = subscriber_user.make()
    membership_recipe = Recipe(
        Membership, user=user, start_date=localdate() - timedelta(days=3)
    )
    membership_recipe.make(
        club=clubs[0], role=baker.make(ClubRole, club=clubs[0], is_board=False)
    )
    membership_recipe.make(
        club=clubs[1], role=baker.make(ClubRole, club=clubs[1], is_board=True)
    )
    membership_recipe.make(
        club=clubs[2], role=baker.make(ClubRole, club=clubs[2], is_board=True)
    )
    membership_recipe.make(
        club=clubs[3],
        role=baker.make(ClubRole, club=clubs[3], is_board=True),
        end_date=localdate() - timedelta(days=1),
    )

    club_ids = Club.objects.having_board_member(user).values_list("id", flat=True)
    assert set(club_ids) == {clubs[1].id, clubs[2].id}


@pytest.mark.parametrize("nb_additional_clubs", [10, 30])
@pytest.mark.parametrize("is_fragment", [True, False])
@pytest.mark.django_db
def test_club_list(client: Client, nb_additional_clubs: int, is_fragment):
    client.force_login(baker.make(User))
    baker.make(Club, _quantity=nb_additional_clubs)
    headers = {"HX-Request": True} if is_fragment else {}
    res = client.get(reverse("club:club_list"), headers=headers)
    assert res.status_code == 200


def assert_club_created(club_name: str):
    club = Club.objects.last()
    assert club.name == club_name
    assert club.board_group.name == f"{club_name} - Bureau"
    assert club.members_group.name == f"{club_name} - Membres"
    # default roles should be added on club creation,
    # whether the creation happens on the admin site or on the user site
    assert list(club.roles.values("name", "is_presidency", "is_board")) == [
        {"name": "Président⸱e", "is_presidency": True, "is_board": True},
        {"name": "Trésorier⸱e", "is_presidency": False, "is_board": True},
        {"name": "Membre actif⸱ve", "is_presidency": False, "is_board": False},
        {"name": "Curieux⸱euse", "is_presidency": False, "is_board": False},
    ]


@pytest.mark.django_db
def test_create_view(admin_client: Client):
    """Test that the club creation view works well"""
    res = admin_client.get(reverse("club:club_new"))
    assert res.status_code == 200
    res = admin_client.post(
        reverse("club:club_new"),
        data={"name": "foo", "parent": settings.SITH_MAIN_CLUB_ID},
    )
    club = Club.objects.last()
    assertRedirects(res, club.get_absolute_url())
    assert_club_created("foo")


@pytest.mark.django_db
def test_default_roles_for_club_with_roles_fails():
    """Test that an Error is raised if trying to create
    default roles for a club that already has roles.
    """
    club = baker.make(Club)
    baker.make(ClubRole, club=club)
    with pytest.raises(ProgrammingError):
        club.create_default_roles()


@pytest.mark.django_db
class TestAdminInterface:
    def test_create(self, admin_client: Client):
        """Test the creation of a club via the admin interface."""
        res = admin_client.post(
            reverse("admin:club_club_add"),
            data={
                "name": "foo",
                "parent": settings.SITH_MAIN_CLUB_ID,
                "address": "Rome",
            },
        )
        assertRedirects(res, reverse("admin:club_club_changelist"))
        assert_club_created("foo")

    def test_change(self, admin_client: Client):
        """Test the edition of a club via the admin interface."""
        club = baker.make(Club)
        res = admin_client.post(
            reverse("admin:club_club_change", kwargs={"object_id": club.id}),
            data={
                "name": "foo",
                "page": club.page_id,
                "home": club.home_id,
                "address": club.address,
            },
        )
        assertRedirects(res, reverse("admin:club_club_changelist"))
        club.refresh_from_db()
        assert club.name == "foo"
        # Club roles shouldn't be modified when editing the club on the admin interface
        # This club had no roles beforehand, therefore it shouldn't have roles now.
        assert not club.roles.exists()
