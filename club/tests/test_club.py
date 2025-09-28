from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from model_bakery.recipe import Recipe

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
