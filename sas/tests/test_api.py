from django.conf import settings
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import RealGroup, User
from sas.models import Album, PeoplePictureRelation, Picture


class TestSas(TestCase):
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


class TestPictureSearch(TestSas):
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


class TestPictureRelation(TestSas):
    def test_delete_relation_route_forbidden(self):
        """Test that unauthorized users are properly 403ed"""
        # take a picture where user_a isn't identified
        relation = PeoplePictureRelation.objects.exclude(user=self.user_a).first()

        res = self.client.delete(f"/api/sas/relation/{relation.id}")
        assert res.status_code == 403

        for user in baker.make(User), self.user_a:
            self.client.force_login(user)
            res = self.client.delete(f"/api/sas/relation/{relation.id}")
            assert res.status_code == 403

    def test_delete_relation_with_authorized_users(self):
        """Test that deletion works as intended when called by an authorized user."""
        relation: PeoplePictureRelation = self.user_a.pictures.first()
        sas_admin_group = RealGroup.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)
        sas_admin = baker.make(User, groups=[sas_admin_group])
        root = baker.make(User, is_superuser=True)
        for user in sas_admin, root, self.user_a:
            with transaction.atomic():
                self.client.force_login(user)
                res = self.client.delete(f"/api/sas/relation/{relation.id}")
                assert res.status_code == 200
                assert not PeoplePictureRelation.objects.filter(pk=relation.id).exists()
                transaction.set_rollback(True)
        public = baker.make(User)
        relation = public.pictures.create(picture=relation.picture)
        self.client.force_login(public)
        res = self.client.delete(f"/api/sas/relation/{relation.id}")
        assert res.status_code == 200
        assert not PeoplePictureRelation.objects.filter(pk=relation.id).exists()

    def test_delete_twice(self):
        """Test a duplicate call on the delete route."""
        self.client.force_login(baker.make(User, is_superuser=True))
        relation = PeoplePictureRelation.objects.first()
        res = self.client.delete(f"/api/sas/relation/{relation.id}")
        assert res.status_code == 200
        relation_count = PeoplePictureRelation.objects.count()
        res = self.client.delete(f"/api/sas/relation/{relation.id}")
        assert res.status_code == 404
        assert PeoplePictureRelation.objects.count() == relation_count
