from datetime import datetime, timedelta

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localtime
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.models import BanGroup, User, UserBan


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
    data = {
        "user": user.id,
        "ban_group": ban_group.id,
        "reason": "Being naughty",
    }
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
def test_remove_ban(client: Client, operator: User):
    client.force_login(operator)
    user = baker.make(User)
    ban = baker.make(UserBan, user=user)
    assert user.bans.exists()
    response = client.post(reverse("rootplace:ban_remove", kwargs={"ban_id": ban.id}))
    assertRedirects(response, expected_url=reverse("rootplace:ban_list"))
    assert not user.bans.exists()
