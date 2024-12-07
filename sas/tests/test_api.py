from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import RealGroup, SithFile, User
from sas.baker_recipes import picture_recipe
from sas.models import Album, PeoplePictureRelation, Picture, PictureModerationRequest


class TestSas(TestCase):
    @classmethod
    def setUpTestData(cls):
        sas = SithFile.objects.get(pk=settings.SITH_SAS_ROOT_DIR_ID)

        Picture.objects.exclude(id=sas.id).delete()
        owner = User.objects.get(username="root")

        cls.user_a = old_subscriber_user.make()
        cls.user_b, cls.user_c = subscriber_user.make(_quantity=2)

        picture = picture_recipe.extend(owner=owner)
        cls.album_a = baker.make(Album, is_in_sas=True, parent=sas)
        cls.album_b = baker.make(Album, is_in_sas=True, parent=sas)
        relation_recipe = Recipe(PeoplePictureRelation)
        relations = []
        for album in cls.album_a, cls.album_b:
            pictures = picture.make(parent=album, _quantity=5, _bulk_create=True)
            relations.extend(
                [
                    relation_recipe.prepare(picture=pictures[1], user=cls.user_a),
                    relation_recipe.prepare(picture=pictures[2], user=cls.user_a),
                    relation_recipe.prepare(picture=pictures[2], user=cls.user_b),
                    relation_recipe.prepare(picture=pictures[3], user=cls.user_b),
                    relation_recipe.prepare(picture=pictures[4], user=cls.user_a),
                    relation_recipe.prepare(picture=pictures[4], user=cls.user_b),
                    relation_recipe.prepare(picture=pictures[4], user=cls.user_c),
                ]
            )
        PeoplePictureRelation.objects.bulk_create(relations)


class TestPictureSearch(TestSas):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("api:pictures")

    def test_anonymous_user_forbidden(self):
        res = self.client.get(self.url)
        assert res.status_code == 403

    def test_filter_by_album(self):
        self.client.force_login(self.user_b)
        res = self.client.get(self.url + f"?album_id={self.album_a.id}")
        assert res.status_code == 200
        expected = list(self.album_a.children_pictures.values_list("id", flat=True))
        assert [i["id"] for i in res.json()["results"]] == expected

    def test_filter_by_user(self):
        self.client.force_login(self.user_b)
        res = self.client.get(self.url + f"?users_identified={self.user_a.id}")
        assert res.status_code == 200
        expected = list(
            self.user_a.pictures.order_by(
                "-picture__parent__date", "picture__date"
            ).values_list("picture_id", flat=True)
        )
        assert [i["id"] for i in res.json()["results"]] == expected

    def test_filter_by_multiple_user(self):
        self.client.force_login(self.user_b)
        res = self.client.get(
            self.url
            + f"?users_identified={self.user_a.id}&users_identified={self.user_b.id}"
        )
        assert res.status_code == 200
        expected = list(
            self.user_a.pictures.union(self.user_b.pictures.all())
            .order_by("-picture__parent__date", "picture__date")
            .values_list("picture_id", flat=True)
        )
        assert [i["id"] for i in res.json()["results"]] == expected

    def test_not_subscribed_user(self):
        """Test that a user that never subscribed can only its own pictures."""
        self.user_a.subscriptions.all().delete()
        self.client.force_login(self.user_a)
        res = self.client.get(f"{self.url}?users_identified={self.user_a.id}")
        assert res.status_code == 200
        expected = list(
            self.user_a.pictures.order_by(
                "-picture__parent__date", "picture__date"
            ).values_list("picture_id", flat=True)
        )
        assert [i["id"] for i in res.json()["results"]] == expected

        # trying to access the pictures of someone else mixed with owned pictures
        # should return only owned pictures
        res = self.client.get(
            self.url
            + f"?users_identified={self.user_a.id}&users_identified={self.user_b.id}"
        )
        assert res.status_code == 200
        assert [i["id"] for i in res.json()["results"]] == expected

        # trying to fetch everything should be the same
        # as fetching its own pictures for a non-subscriber
        res = self.client.get(self.url)
        assert res.status_code == 200
        assert [i["id"] for i in res.json()["results"]] == expected

        # trying to access the pictures of someone else should return only
        # the ones where the non-subscribed user is identified too
        res = self.client.get(f"{self.url}?users_identified={self.user_b.id}")
        assert res.status_code == 200
        expected = list(
            self.user_b.pictures.intersection(self.user_a.pictures.all())
            .order_by("-picture__parent__date", "picture__date")
            .values_list("picture_id", flat=True)
        )
        assert [i["id"] for i in res.json()["results"]] == expected

    def test_num_queries(self):
        """Test that the number of queries is stable."""
        self.client.force_login(subscriber_user.make())
        cache.clear()
        with self.assertNumQueries(7):
            # 2 requests to create the session
            # 1 request to fetch the user from the db
            # 2 requests to check the user permissions, depends on the db engine
            # 1 request to fetch the pictures
            # 1 request to count the total number of items in the pagination
            self.client.get(self.url)


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


class TestPictureModeration(TestSas):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sas_admin = baker.make(
            User, groups=[RealGroup.objects.get(pk=settings.SITH_GROUP_SAS_ADMIN_ID)]
        )
        cls.picture = Picture.objects.filter(parent=cls.album_a)[0]
        cls.picture.is_moderated = False
        cls.picture.asked_for_removal = True
        cls.picture.save()
        cls.url = reverse("api:picture_moderate", kwargs={"picture_id": cls.picture.id})
        baker.make(PictureModerationRequest, picture=cls.picture, author=cls.user_a)

    def test_moderation_route_forbidden(self):
        """Test that basic users (even if owner) cannot moderate a picture."""
        self.picture.owner = self.user_b

        for user in baker.make(User), subscriber_user.make(), self.user_b:
            self.client.force_login(user)
            res = self.client.patch(self.url)
            assert res.status_code == 403

    def test_moderation_route_authorized(self):
        """Test that sas admins can moderate a picture."""
        self.client.force_login(self.sas_admin)
        res = self.client.patch(self.url)
        assert res.status_code == 200
        self.picture.refresh_from_db()
        assert self.picture.is_moderated
        assert not self.picture.asked_for_removal
        assert not self.picture.moderation_requests.exists()

    def test_get_moderation_requests(self):
        """Test that fetching moderation requests work."""

        url = reverse(
            "api:picture_moderation_requests", kwargs={"picture_id": self.picture.id}
        )
        self.client.force_login(self.sas_admin)
        res = self.client.get(url)
        assert res.status_code == 200
        assert len(res.json()) == 1
        assert res.json()[0]["author"]["id"] == self.user_a.id
