#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
from typing import Callable

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import RealGroup, User
from sas.baker_recipes import picture_recipe
from sas.models import Album

# Create your tests here.


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_factory",
    [
        subscriber_user.make,
        old_subscriber_user.make,
        lambda: baker.make(User, is_superuser=True),
        lambda: baker.make(
            User, groups=[RealGroup.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
        ),
        lambda: baker.make(User),
    ],
)
def test_load_main_page(client: Client, user_factory: Callable[[], User]):
    """Just check that the SAS doesn't crash."""
    user = user_factory()
    client.force_login(user)
    res = client.get(reverse("sas:main"))
    assert res.status_code == 200


@pytest.mark.django_db
def test_album_access_non_subscriber(client: Client):
    """Test that non-subscribers can only access albums where they are identified."""
    album = baker.make(Album, parent_id=settings.SITH_SAS_ROOT_DIR_ID)
    user = baker.make(User)
    client.force_login(user)
    res = client.get(reverse("sas:album", kwargs={"album_id": album.id}))
    assert res.status_code == 403

    picture = picture_recipe.make(parent=album)
    picture.people.create(user=user)
    cache.clear()
    res = client.get(reverse("sas:album", kwargs={"album_id": album.id}))
    assert res.status_code == 200
