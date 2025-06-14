#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
from typing import Callable

import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertHTMLEqual, assertInHTML, assertRedirects

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import Group, User
from sas.baker_recipes import picture_recipe
from sas.models import Album, Picture

# Create your tests here.


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_factory",
    [
        subscriber_user.make,
        old_subscriber_user.make,
        lambda: baker.make(User, is_superuser=True),
        lambda: baker.make(
            User, groups=[Group.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
        ),
        lambda: baker.make(User),
        lambda: None,
    ],
)
def test_load_main_page(client: Client, user_factory: Callable[[], User]):
    """Just check that the SAS doesn't crash."""
    user = user_factory()
    if user is not None:
        client.force_login(user)
    res = client.get(reverse("sas:main"))
    assert res.status_code == 200


@pytest.mark.django_db
def test_main_page_no_form_for_regular_users(client: Client):
    """Test that subscribed users see no form on the sas main page"""
    client.force_login(subscriber_user.make())
    res = client.get(reverse("sas:main"))
    soup = BeautifulSoup(res.text, "lxml")
    forms = soup.find("main").find_all("form")
    assert len(forms) == 0


@pytest.mark.django_db
def test_main_page_content_anonymous(client: Client):
    """Test that public users see only an incentive to login"""
    res = client.get(reverse("sas:main"))
    soup = BeautifulSoup(res.text, "lxml")
    expected = "<h3>SAS</h3><p>Vous devez être connecté pour voir les photos.</p>"
    assertHTMLEqual(soup.find("main").decode_contents(), expected)


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


@pytest.mark.django_db
class TestAlbumUpload:
    @staticmethod
    def assert_album_created(response, name, parent):
        assert response.headers.get("HX-Redirect", "") == parent.get_absolute_url()
        children = list(Album.objects.filter(parent=parent))
        assert len(children) == 1
        assert children[0].name == name

    def test_sas_admin(self, client: Client):
        user = baker.make(
            User, groups=[Group.objects.get(id=settings.SITH_GROUP_SAS_ADMIN_ID)]
        )
        album = baker.make(Album, parent_id=settings.SITH_SAS_ROOT_DIR_ID)
        client.force_login(user)
        response = client.post(
            reverse("sas:album_create"), {"name": "new", "parent": album.id}
        )
        self.assert_album_created(response, "new", album)

    def test_non_admin_user_with_edit_rights_on_parent(self, client: Client):
        group = baker.make(Group)
        user = subscriber_user.make(groups=[group])
        album = baker.make(
            Album, parent_id=settings.SITH_SAS_ROOT_DIR_ID, edit_groups=[group]
        )
        client.force_login(user)
        response = client.post(
            reverse("sas:album_create"), {"name": "new", "parent": album.id}
        )
        self.assert_album_created(response, "new", album)

    def test_permission_denied(self, client: Client):
        album = baker.make(Album, parent_id=settings.SITH_SAS_ROOT_DIR_ID)
        client.force_login(subscriber_user.make())
        response = client.post(
            reverse("sas:album_create"), {"name": "new", "parent": album.id}
        )
        errors = BeautifulSoup(response.text, "lxml").find_all(class_="errorlist")
        assert len(errors) == 1
        assert errors[0].text == "Vous n'avez pas la permission de faire cela"
        assert not album.children.exists()


class TestSasModeration(TestCase):
    @classmethod
    def setUpTestData(cls):
        album = baker.make(
            Album, parent_id=settings.SITH_SAS_ROOT_DIR_ID, is_moderated=True
        )
        cls.pictures = picture_recipe.make(
            parent=album, _quantity=10, _bulk_create=True
        )
        cls.to_moderate = cls.pictures[0]
        cls.to_moderate.is_moderated = False
        cls.to_moderate.save()
        cls.moderator = baker.make(
            User, groups=[Group.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
        )
        cls.simple_user = subscriber_user.make()

    def setUp(self):
        cache.clear()

    def test_moderation_page_sas_admin(self):
        """Test that a moderator can see the pictures needing moderation."""
        self.client.force_login(self.moderator)
        res = self.client.get(reverse("sas:moderation"))
        assert res.status_code == 200
        assert len(res.context_data["pictures"]) == 1
        assert res.context_data["pictures"][0] == self.to_moderate

        res = self.client.post(
            reverse("sas:moderation"),
            data={"album_id": self.to_moderate.id, "picture_id": self.to_moderate.id},
        )

    def test_moderation_page_forbidden(self):
        self.client.force_login(self.simple_user)
        res = self.client.get(reverse("sas:moderation"))
        assert res.status_code == 403

    def test_moderate_picture(self):
        self.client.force_login(self.moderator)
        res = self.client.get(
            reverse("core:file_moderate", kwargs={"file_id": self.to_moderate.id}),
            data={"next": self.pictures[1].get_absolute_url()},
        )
        assertRedirects(res, self.pictures[1].get_absolute_url())
        self.to_moderate.refresh_from_db()
        assert self.to_moderate.is_moderated

    def test_delete_picture(self):
        self.client.force_login(self.moderator)
        res = self.client.post(
            reverse("core:file_delete", kwargs={"file_id": self.to_moderate.id})
        )
        assert res.status_code == 302
        assert not Picture.objects.filter(pk=self.to_moderate.id).exists()

    def test_moderation_action_non_authorized_user(self):
        """Test that a non-authorized user cannot moderate a picture."""
        self.client.force_login(self.simple_user)
        res = self.client.post(
            reverse("core:file_moderate", kwargs={"file_id": self.to_moderate.id}),
        )
        assert res.status_code == 403
        self.to_moderate.refresh_from_db()
        assert not self.to_moderate.is_moderated
        res = self.client.post(
            reverse("core:file_delete", kwargs={"file_id": self.to_moderate.id}),
        )
        assert res.status_code == 403
        assert Picture.objects.filter(pk=self.to_moderate.id).exists()

    def test_request_moderation_form_access(self):
        """Test that regular can access the form to ask for moderation."""
        self.client.force_login(self.simple_user)
        res = self.client.get(
            reverse(
                "sas:picture_ask_removal", kwargs={"picture_id": self.pictures[1].id}
            ),
        )
        assert res.status_code == 200

    def test_request_moderation_form_submit(self):
        """Test that moderation requests are created."""
        self.client.force_login(self.simple_user)
        message = "J'aime pas cette photo (ni la Cocarde)."
        url = reverse(
            "sas:picture_ask_removal", kwargs={"picture_id": self.pictures[1].id}
        )
        res = self.client.post(url, data={"reason": message})
        assertRedirects(
            res, reverse("sas:album", kwargs={"album_id": self.pictures[1].parent_id})
        )
        assert self.pictures[1].moderation_requests.count() == 1
        assert self.pictures[1].moderation_requests.first().reason == message

        # test that the user cannot ask for moderation twice
        res = self.client.post(url, data={"reason": message})
        assert res.status_code == 200
        assert self.pictures[1].moderation_requests.count() == 1
        assertInHTML(
            '<ul class="errorlist nonfield"><li>'
            "Vous avez déjà déposé une demande de retrait pour cette photo.</li></ul>",
            res.text,
        )


@pytest.mark.django_db
class TestUserPicture:
    def test_anonymous_user_unauthorized(self, client):
        """An anonymous user shouldn't have access to an user's photo page."""
        response = client.get(
            reverse(
                "sas:user_pictures",
                kwargs={"user_id": User.objects.get(username="sli").pk},
            )
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        ("username", "status"),
        [
            ("guy", 403),
            ("root", 200),
            ("skia", 200),
            ("sli", 200),
        ],
    )
    def test_page_is_working(self, client, username, status):
        """Only user that subscribed (or admins) should be able to see the page."""
        # Test for simple user
        client.force_login(User.objects.get(username=username))
        response = client.get(
            reverse(
                "sas:user_pictures",
                kwargs={"user_id": User.objects.get(username="sli").pk},
            )
        )
        assert response.status_code == status
