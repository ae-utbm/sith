from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import User
from sas.models import Album, PeoplePictureRelation, Picture


class SasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Picture.objects.all().delete()
        owner = User.objects.get(username="root")

        cls.user_a = old_subscriber_user.make()
        cls.user_b, cls.user_c = subscriber_user.make(_quantity=2)

        picture_recipe = Recipe(
            Picture, is_in_sas=True, is_folder=False, owner=owner, is_moderated=True
        )
        cls.album_a = baker.make(Album, is_in_sas=True)
        cls.album_b = baker.make(Album, is_in_sas=True)
        for album in cls.album_a, cls.album_b:
            pictures = picture_recipe.make(parent=album, _quantity=5, _bulk_create=True)
            baker.make(PeoplePictureRelation, picture=pictures[1], user=cls.user_a)
            baker.make(PeoplePictureRelation, picture=pictures[2], user=cls.user_a)
            baker.make(PeoplePictureRelation, picture=pictures[2], user=cls.user_b)
            baker.make(PeoplePictureRelation, picture=pictures[3], user=cls.user_b)
            baker.make(PeoplePictureRelation, picture=pictures[4], user=cls.user_a)
            baker.make(PeoplePictureRelation, picture=pictures[4], user=cls.user_b)
            baker.make(PeoplePictureRelation, picture=pictures[4], user=cls.user_c)

    def test_anonymous_user_forbidden(self):
        res = self.client.get(reverse("api:pictures"))
        assert res.status_code == 403

    def test_filter_by_album(self):
        self.client.force_login(self.user_b)
        res = self.client.get(reverse("api:pictures") + f"?album_id={self.album_a.id}")
        assert res.status_code == 200
        expected = list(
            self.album_a.children_pictures.order_by("-date").values_list(
                "id", flat=True
            )
        )
        assert [i["id"] for i in res.json()] == expected

    def test_filter_by_user(self):
        self.client.force_login(self.user_b)
        res = self.client.get(
            reverse("api:pictures") + f"?users_identified={self.user_a.id}"
        )
        assert res.status_code == 200
        expected = list(
            self.user_a.pictures.order_by("-picture__date").values_list(
                "picture_id", flat=True
            )
        )
        assert [i["id"] for i in res.json()] == expected

    def test_filter_by_multiple_user(self):
        self.client.force_login(self.user_b)
        res = self.client.get(
            reverse("api:pictures")
            + f"?users_identified={self.user_a.id}&users_identified={self.user_b.id}"
        )
        assert res.status_code == 200
        expected = list(
            self.user_a.pictures.union(self.user_b.pictures.all())
            .order_by("-picture__date")
            .values_list("picture_id", flat=True)
        )
        assert [i["id"] for i in res.json()] == expected

    def test_not_subscribed_user(self):
        """Test that a user that is not subscribed can only its own pictures."""
        self.client.force_login(self.user_a)
        res = self.client.get(
            reverse("api:pictures") + f"?users_identified={self.user_a.id}"
        )
        assert res.status_code == 200
        expected = list(
            self.user_a.pictures.order_by("-picture__date").values_list(
                "picture_id", flat=True
            )
        )
        assert [i["id"] for i in res.json()] == expected

        # trying to access the pictures of someone else
        res = self.client.get(
            reverse("api:pictures") + f"?users_identified={self.user_b.id}"
        )
        assert res.status_code == 403

        # trying to access the pictures of someone else shouldn't success,
        # even if mixed with owned pictures
        res = self.client.get(
            reverse("api:pictures")
            + f"?users_identified={self.user_a.id}&users_identified={self.user_b.id}"
        )
        assert res.status_code == 403
