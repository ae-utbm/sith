from io import BytesIO
from itertools import cycle
from typing import Callable
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe, foreign_key
from PIL import Image
from pytest_django.asserts import assertNumQueries

from core.baker_recipes import board_user, old_subscriber_user, subscriber_user
from core.models import Group, SithFile, User
from sas.models import Picture
from sith import settings


@pytest.mark.django_db
class TestImageAccess:
    @pytest.mark.parametrize(
        "user_factory",
        [
            lambda: baker.make(User, is_superuser=True),
            lambda: baker.make(
                User, groups=[Group.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
            ),
            lambda: baker.make(
                User, groups=[Group.objects.get(pk=settings.SITH_GROUP_COM_ADMIN_ID)]
            ),
        ],
    )
    def test_sas_image_access(self, user_factory: Callable[[], User]):
        """Test that only authorized users can access the sas image."""
        user = user_factory()
        picture: SithFile = baker.make(
            Picture, parent=SithFile.objects.get(pk=settings.SITH_SAS_ROOT_DIR_ID)
        )
        assert picture.is_owned_by(user)

    def test_sas_image_access_owner(self):
        """Test that the owner of the image can access it."""
        user = baker.make(User)
        picture: Picture = baker.make(Picture, owner=user)
        assert picture.is_owned_by(user)

    @pytest.mark.parametrize(
        "user_factory",
        [
            lambda: baker.make(User),
            subscriber_user.make,
            old_subscriber_user.make,
            board_user.make,
        ],
    )
    def test_sas_image_access_forbidden(self, user_factory: Callable[[], User]):
        cache.clear()
        user = user_factory()
        owner = baker.make(User)
        picture: Picture = baker.make(Picture, owner=owner)
        assert not picture.is_owned_by(user)


# TODO: many tests on the pages:
#   - renaming a page
#   - changing a page's parent --> check that page's children's full_name
#   - changing the different groups of the page


class TestFileHandling(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.subscriber = User.objects.get(username="subscriber")

    def setUp(self):
        self.client.login(username="subscriber", password="plop")

    def test_create_folder_home(self):
        response = self.client.post(
            reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id}),
            {"folder_name": "GUY_folder_test"},
        )
        assert response.status_code == 302
        response = self.client.get(
            reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id})
        )
        assert response.status_code == 200
        assert "GUY_folder_test</a>" in str(response.content)

    def test_upload_file_home(self):
        with open("/bin/ls", "rb") as f:
            response = self.client.post(
                reverse(
                    "core:file_detail", kwargs={"file_id": self.subscriber.home.id}
                ),
                {"file_field": f},
            )
        assert response.status_code == 302
        response = self.client.get(
            reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id})
        )
        assert response.status_code == 200
        assert "ls</a>" in str(response.content)


@pytest.mark.django_db
class TestFileModerationView:
    """Test access to file moderation view"""

    @pytest.mark.parametrize(
        ("user_factory", "status_code"),
        [
            (lambda: None, 403),  # Anonymous user
            (lambda: baker.make(User, is_superuser=True), 200),
            (lambda: baker.make(User), 403),
            (lambda: subscriber_user.make(), 403),
            (lambda: old_subscriber_user.make(), 403),
            (lambda: board_user.make(), 403),
        ],
    )
    def test_view_access(
        self, client: Client, user_factory: Callable[[], User | None], status_code: int
    ):
        user = user_factory()
        if user:  # if None, then it's an anonymous user
            client.force_login(user_factory())
        assert client.get(reverse("core:file_moderation")).status_code == status_code


@pytest.mark.django_db
class TestUserProfilePicture:
    """Test interactions with user's profile picture."""

    @pytest.fixture
    def user(self) -> User:
        pict = foreign_key(Recipe(SithFile), one_to_one=True)
        return subscriber_user.extend(profile_pict=pict).make()

    @staticmethod
    def delete_picture_request(user: User, client: Client):
        return client.post(
            reverse(
                "core:file_delete",
                kwargs={"file_id": user.profile_pict.pk, "popup": ""},
            )
            + f"?next={user.get_absolute_url()}"
        )

    @pytest.mark.parametrize(
        "user_factory",
        [lambda: baker.make(User, is_superuser=True), board_user.make],
    )
    def test_delete_picture_successful(
        self, user: User, user_factory: Callable[[], User], client: Client
    ):
        """Test that root and board members can delete a user's profile picture."""
        cache.clear()
        operator = user_factory()
        client.force_login(operator)
        res = self.delete_picture_request(user, client)
        assert res.status_code == 302
        assert res.url == user.get_absolute_url()
        user.refresh_from_db()
        assert user.profile_pict is None

    @pytest.mark.parametrize(
        "user_factory",
        [lambda: baker.make(User), subscriber_user.make],
    )
    def test_delete_picture_unauthorized(
        self, user: User, user_factory, client: Client
    ):
        """Test that regular users can't delete a user's profile picture."""
        cache.clear()
        operator = user_factory()
        client.force_login(operator)
        original_picture = user.profile_pict
        res = self.delete_picture_request(user, client)
        assert res.status_code == 403
        user.refresh_from_db()
        assert user.profile_pict is not None
        assert user.profile_pict == original_picture

    def test_user_cannot_delete_own_picture(self, user: User, client: Client):
        """Test that a user can't delete their own profile picture."""
        cache.clear()
        client.force_login(user)
        original_picture = user.profile_pict
        res = self.delete_picture_request(user, client)
        assert res.status_code == 403
        user.refresh_from_db()
        assert user.profile_pict is not None
        assert user.profile_pict == original_picture

    def test_user_set_own_picture(self, user: User, client: Client):
        """Test that a user can set their own profile picture if they have none."""
        user.profile_pict.delete()
        user.profile_pict = None
        user.save()
        cache.clear()
        client.force_login(user)
        img = Image.new("RGB", (10, 10))
        content = BytesIO()
        img.save(content, format="JPEG")
        name = str(uuid4())
        res = client.post(
            reverse("core:user_edit", kwargs={"user_id": user.pk}),
            data={
                # birthdate, email and tshirt_size are required by the form
                "date_of_birth": "1990-01-01",
                "email": f"{uuid4()}@gmail.com",
                "tshirt_size": "M",
                "profile_pict": SimpleUploadedFile(
                    f"{name}.jpg", content.getvalue(), content_type="image/jpeg"
                ),
            },
        )
        assert res.status_code == 302
        user.refresh_from_db()
        assert user.profile_pict is not None
        # uploaded images should be converted to WEBP
        assert Image.open(user.profile_pict.file).format == "WEBP"


@pytest.mark.django_db
def test_apply_rights_recursively():
    """Test that the apply_rights_recursively method works as intended."""
    files = [baker.make(SithFile)]
    files.extend(baker.make(SithFile, _quantity=3, parent=files[0], _bulk_create=True))
    files.extend(
        baker.make(SithFile, _quantity=3, parent=iter(files[1:4]), _bulk_create=True)
    )
    files.extend(
        baker.make(SithFile, _quantity=6, parent=cycle(files[4:7]), _bulk_create=True)
    )

    groups = list(baker.make(Group, _quantity=7))
    files[0].view_groups.set(groups[:3])
    files[0].edit_groups.set(groups[2:6])

    # those groups should be erased after the function call
    files[1].view_groups.set(groups[6:])

    with assertNumQueries(10):
        # 1 query for each level of depth (here 4)
        # 1 query to get the view_groups of the first file
        # 1 query to delete the previous view_groups
        # 1 query apply the new view_groups
        # same 3 queries for the edit_groups
        files[0].apply_rights_recursively()
    for file in SithFile.objects.filter(pk__in=[f.pk for f in files]).prefetch_related(
        "view_groups", "edit_groups"
    ):
        assert set(file.view_groups.all()) == set(groups[:3])
        assert set(file.edit_groups.all()) == set(groups[2:6])
