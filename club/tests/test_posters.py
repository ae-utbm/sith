import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from club.models import Club
from com.models import Poster
from core.baker_recipes import subscriber_user


@pytest.mark.django_db
@pytest.mark.parametrize("route_url", ["club:poster_list", "club:poster_create"])
def test_access(client: Client, route_url):
    club = baker.make(Club)
    user = subscriber_user.make()
    url = reverse(route_url, kwargs={"club_id": club.id})

    client.force_login(user)
    assert client.get(url).status_code == 403
    club.board_group.users.add(user)
    assert client.get(url).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("route_url", ["club:poster_edit", "club:poster_delete"])
def test_access_specific_poster(client: Client, route_url):
    club = baker.make(Club)
    user = subscriber_user.make()
    poster = baker.make(Poster)
    url = reverse(route_url, kwargs={"club_id": club.id, "poster_id": poster.id})

    client.force_login(user)
    assert client.get(url).status_code == 403
    club.board_group.users.add(user)
    assert client.get(url).status_code == 200
