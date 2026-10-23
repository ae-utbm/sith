from typing import TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.urls import reverse
from model_bakery import baker

from core.models import User

if TYPE_CHECKING:
    from django.test import Client


@pytest.mark.django_db
@pytest.mark.parametrize("can_save", [True, False])
def test_generator_ok(client: Client, can_save):
    user = baker.make(User)
    if can_save:
        user.user_permissions.add(Permission.objects.get(codename="add_self_timetable"))
    client.force_login(user)

    res = client.get(reverse("timetable:generator"))
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    elem = soup.find(id="timetable-save")

    if can_save:
        assert elem is not None
    else:
        assert elem is None
