import pytest
from model_bakery import baker, seq
from model_bakery.recipe import Recipe

from club.models import Club, ClubRole


@pytest.mark.django_db
def test_order_auto():
    """Test that newly created roles are put in the right place."""
    club = baker.make(Club)
    recipe = Recipe(ClubRole, club=club, name=seq("role "))
    # bulk create initial roles
    roles = recipe.make(
        is_board=iter([True, True, False]),
        is_presidency=iter([True, False, False]),
        order=iter([1, 2, 3]),
        _quantity=3,
        _bulk_create=True,
    )
    # then create the remaining roles one by one (like they will be in prod)
    # each new role should be placed at the end of its category
    role_a = recipe.make(is_board=True, is_presidency=True, order=None)
    role_b = recipe.make(is_board=True, is_presidency=False, order=None)
    role_c = recipe.make(is_board=False, is_presidency=False, order=None)
    assert list(club.roles.order_by("order")) == [
        roles[0],
        role_a,
        roles[1],
        role_b,
        roles[2],
        role_c,
    ]
