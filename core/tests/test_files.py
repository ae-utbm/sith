from io import BytesIO
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

from core.baker_recipes import board_user, subscriber_user
from core.models import SithFile, User


@pytest.mark.django_db
class TestUserPicture:
    def test_anonymous_user_unauthorized(self, client):
        """An anonymous user shouldn't have access to an user's photo page."""
        response = client.get(
            reverse(
                "core:user_pictures",
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
                "core:user_pictures",
                kwargs={"user_id": User.objects.get(username="sli").pk},
            )
        )
        assert response.status_code == status


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
