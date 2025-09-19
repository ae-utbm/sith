from datetime import timedelta

import pytest
from django.utils.timezone import localdate
from model_bakery import baker
from model_bakery.recipe import Recipe

from club.models import Club, Membership
from core.baker_recipes import subscriber_user


@pytest.mark.django_db
def test_club_queryset_having_board_member():
    clubs = baker.make(Club, _quantity=5)
    user = subscriber_user.make()
    membership_recipe = Recipe(
        Membership, user=user, start_date=localdate() - timedelta(days=3)
    )
    membership_recipe.make(club=clubs[0], role=1)
    membership_recipe.make(club=clubs[1], role=3)
    membership_recipe.make(club=clubs[2], role=7)
    membership_recipe.make(
        club=clubs[3], role=3, end_date=localdate() - timedelta(days=1)
    )

    club_ids = Club.objects.having_board_member(user).values_list("id", flat=True)
    assert set(club_ids) == {clubs[1].id, clubs[2].id}
