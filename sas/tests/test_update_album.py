import random
import string
from pathlib import Path
from typing import Callable
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.timezone import localdate
from model_bakery import baker
from PIL import Image
from pytest_django.asserts import assertInHTML, assertRedirects

from core.baker_recipes import subscriber_user
from core.models import Group, User
from core.utils import RED_PIXEL_PNG
from sas.baker_recipes import picture_recipe
from sas.forms import AlbumEditForm
from sas.models import Album


@pytest.fixture
def sas_root(db) -> Album:
    return Album.objects.get(id=settings.SITH_SAS_ROOT_DIR_ID)


@pytest.fixture
def album(db) -> Album:
    name = "".join(
        random.choice(string.ascii_letters) for _ in range(Album.NAME_MAX_LENGTH)
    )
    return baker.make(
        Album, name=name, parent_id=settings.SITH_SAS_ROOT_DIR_ID, is_moderated=True
    )


@pytest.mark.parametrize("user", [None, lambda: baker.make(User), subscriber_user.make])
@pytest.mark.django_db
def test_permission_denied(
    client: Client, album: Album, user: Callable[[], User] | None
):
    if user:
        client.force_login(user())
    url = reverse("sas:album_edit", kwargs={"album_id": album.pk})
    for method in client.get, client.post:
        assert method(url).status_code == 403


@pytest.mark.django_db
def test_sas_root_read_only(client: Client, sas_root: Album):
    moderator = baker.make(
        User, groups=[Group.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
    )
    client.force_login(moderator)
    url = reverse("sas:album_edit", kwargs={"album_id": sas_root.pk})
    for method in client.get, client.post:
        assert method(url).status_code == 404


@pytest.mark.parametrize(
    ("excluded", "is_valid"),
    [
        ("name", False),
        ("date", False),
        ("file", True),
        ("parent", False),
        ("edit_groups", True),
        ("recursive", True),
    ],
)
@pytest.mark.django_db
def test_form_required(album: Album, excluded: str, is_valid: bool):  # noqa: FBT001
    data = {
        "name": album.name,
        "parent": baker.make(Album, parent=album.parent, is_moderated=True).pk,
        "date": localdate(),
        "file": "/random/path",
        "edit_groups": [settings.SITH_GROUP_SAS_ADMIN_ID],
        "recursive": False,
    }
    del data[excluded]
    assert AlbumEditForm(data=data).is_valid() == is_valid


@pytest.mark.django_db
def test_form_album_name(album: Album):
    data = {
        "name": "a" * Album.NAME_MAX_LENGTH,
        "parent": album.pk,
        "date": localdate(),
    }
    assert AlbumEditForm(data=data).is_valid()

    data["name"] = "a" * (Album.NAME_MAX_LENGTH + 1)
    assert not AlbumEditForm(data=data).is_valid()


@pytest.mark.django_db
def test_update_recursive_parent(client: Client, album: Album):
    client.force_login(baker.make(User, is_superuser=True))

    payload = {"name": album.name, "parent": album.pk, "date": localdate()}
    response = client.post(
        reverse("sas:album_edit", kwargs={"album_id": album.pk}), payload
    )
    assertInHTML("<li>Boucle dans l'arborescence des dossiers</li>", response.text)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "user",
    [
        lambda: baker.make(User, is_superuser=True),
        lambda: baker.make(
            User, groups=[Group.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
        ),
    ],
)
@pytest.mark.parametrize(
    "parent",
    [
        lambda: baker.make(
            Album, parent_id=settings.SITH_SAS_ROOT_DIR_ID, is_moderated=True
        ),
        lambda: Album.objects.get(id=settings.SITH_SAS_ROOT_DIR_ID),
    ],
)
@pytest.mark.django_db
def test_update(
    client: Client,
    album: Album,
    sas_root: Album,
    user: Callable[[], User],
    parent: Callable[[], Album],
):
    client.force_login(user())
    expected_redirect = reverse("sas:album", kwargs={"album_id": album.pk})
    payload = {
        "name": "foo",
        "parent": parent().id,
        "date": localdate(),
        "recursive": False,
    }
    response = client.post(
        reverse("sas:album_edit", kwargs={"album_id": album.pk}), payload
    )
    assertRedirects(response, expected_redirect)
    album.refresh_from_db()
    assert album.name == "foo"
    assert album.parent.id == payload["parent"]
    assert localdate(album.date) == localdate()


class TestAlbumThumbnail:
    @pytest.fixture
    def files(self):
        return MultiValueDict(
            {"file": [SimpleUploadedFile(name="foo.png", content=RED_PIXEL_PNG)]}
        )

    def test_thumbnail_resized(self, album, files):
        """Test that album thumbnails are resized to the correct dimensions."""
        form = AlbumEditForm(
            data={"name": album.name, "date": localdate(), "parent": album.parent.id},
            files=files,
            instance=album,
        )
        assert form.is_valid()
        form.save()
        album.refresh_from_db()
        assert album.file.name == f"SAS/{album.name}/thumb.webp"
        assert Image.open(album.file).size == (200, 200)

    def test_thumbnail_removed(self, album):
        """Test the case where the user checks the box to remove the thumbnail"""
        album.file = ContentFile(name="foo.png", content=RED_PIXEL_PNG)
        album.save()
        previous_filename = album.file.name
        form = AlbumEditForm(
            data={
                "name": "foo",
                "date": localdate(),
                "parent": album.parent.id,
                "file-clear": True,
            },
            instance=album,
        )
        # as there is now no picture, a thumbnail should be generated
        with patch.object(Album, "generate_thumbnail") as mock:
            assert form.is_valid()
            form.save()
            album.refresh_from_db()
            assert album.file.storage.exists(album.file.name)
            assert not album.file.storage.exists(previous_filename)
            mock.assert_called_once()

    def test_generate_thumbnail(self, album):
        """Test that if no image is given and the album has pictures,
        the thumbnail is automatically generated.
        """
        picture = picture_recipe.make(
            parent=album, thumbnail=ContentFile(name="foo.png", content=RED_PIXEL_PNG)
        )
        form = AlbumEditForm(
            data={"name": "foo", "date": localdate(), "parent": album.parent.id},
            instance=album,
        )
        assert form.is_valid()
        form.save()
        album.refresh_from_db()
        assert Path(album.file.name) == Path("SAS/foo/thumb.webp")
        assert album.file.storage.exists(album.file.name)
        assert Image.open(album.file) == Image.open(picture.thumbnail)
