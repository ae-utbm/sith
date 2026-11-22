from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.timezone import localdate, localtime
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.models import ClubRole, Membership
from core.baker_recipes import subscriber_user
from core.models import BanGroup, User, UserBan
from counter.models import Counter
from sith import settings

if TYPE_CHECKING:
    from django.test import Client


@pytest.fixture
def operator(db) -> User:
    return baker.make(
        User,
        user_permissions=Permission.objects.filter(
            codename__in=["view_userban", "add_userban", "delete_userban"]
        ),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expires_at",
    [None, localtime().replace(second=0, microsecond=0) + timedelta(days=7)],
)
def test_ban_user(client: Client, operator: User, expires_at: datetime):
    client.force_login(operator)
    user = baker.make(User)
    ban_group = BanGroup.objects.first()
    data = {"user": user.id, "ban_group": ban_group.id, "reason": "Being naughty"}
    if expires_at is not None:
        data["expires_at"] = expires_at.strftime("%Y-%m-%d %H:%M")
    response = client.post(reverse("rootplace:ban_create"), data)
    assertRedirects(response, expected_url=reverse("rootplace:ban_list"))
    bans = list(user.bans.all())
    assert len(bans) == 1
    assert bans[0].expires_at == expires_at
    assert bans[0].reason == "Being naughty"
    assert bans[0].ban_group == ban_group


@pytest.mark.django_db
def test_ban_counter_ends_barmanship():
    user = subscriber_user.make()
    counter = baker.make(Counter)
    counter.sellers.add(user, through_defaults={"is_regular": True})

    UserBan.objects.create(
        user=user,
        ban_group_id=settings.SITH_GROUP_BANNED_SUBSCRIPTION_ID,
        reason="ban comptoir",
    )

    # check that we did effectively delete the barmanship
    # and not the bar itself (better safe than sorry)
    assert Counter.objects.filter(id=counter.id).exists()
    assert not user.counters.exists()


@pytest.mark.django_db
def test_ban_responsability_ends_board_memberships():
    user = subscriber_user.make()
    roles = baker.make(ClubRole, is_board=iter([False, True]), _quantity=2)
    membership = baker.make(
        Membership, role=roles[0], club=roles[0].club, user=user, end_date=None
    )
    board_membership = baker.make(
        Membership, role=roles[1], club=roles[1].club, user=user, end_date=None
    )
    UserBan.objects.create(
        user=user,
        ban_group_id=settings.SITH_GROUP_BANNED_RESPONSIBILITY_ID,
        reason="ban responsabilités",
    )
    # only the board membership should be concluded
    membership.refresh_from_db()
    assert not membership.end_date
    board_membership.refresh_from_db()
    assert board_membership.end_date == localdate()


@pytest.mark.django_db
def test_remove_ban(client: Client, operator: User):
    client.force_login(operator)
    user = baker.make(User)
    ban = baker.make(UserBan, user=user)
    assert user.bans.exists()
    response = client.post(reverse("rootplace:ban_remove", kwargs={"ban_id": ban.id}))
    assertRedirects(response, expected_url=reverse("rootplace:ban_list"))
    assert not user.bans.exists()
