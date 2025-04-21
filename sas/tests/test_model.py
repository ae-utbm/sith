import pytest
from django.test import TestCase
from model_bakery import baker

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import User
from sas.baker_recipes import album_recipe, picture_recipe
from sas.models import Album, PeoplePictureRelation, Picture


class TestPictureQuerySet(TestCase):
    @classmethod
    def setUpTestData(cls):
        Picture.objects.all().delete()
        cls.pictures = picture_recipe.make(_quantity=10, _bulk_create=True)
        Picture.objects.filter(pk=cls.pictures[0].id).update(is_moderated=False)

    def test_root(self):
        root = baker.make(User, is_superuser=True)
        pictures = list(Picture.objects.viewable_by(root).order_by("id"))
        assert pictures == self.pictures

    def test_subscriber(self):
        """Test that subscribed users see moderated pictures and pictures they own."""
        subscriber = subscriber_user.make()
        old_subcriber = old_subscriber_user.make()
        qs = Picture.objects.filter(pk=self.pictures[1].id)
        qs.update(is_moderated=False)
        for user in (subscriber, old_subcriber):
            qs.update(owner=user)
            pictures = list(Picture.objects.viewable_by(user).order_by("id"))
            assert pictures == self.pictures[1:]

    def test_not_subscribed_identified(self):
        """Public users should only see moderated photos on which they are identified."""
        user = baker.make(
            # This is the guy who asked the feature of making pictures
            # available for tagged users, even if not subscribed
            User,
            first_name="Pierrick",
            last_name="Dheilly",
            nick_name="Sahmer",
        )
        user.pictures.create(picture=self.pictures[0])  # non-moderated
        user.pictures.create(picture=self.pictures[1])  # moderated
        pictures = list(Picture.objects.viewable_by(user))
        assert pictures == [self.pictures[1]]


@pytest.mark.django_db
def test_identifications_viewable_by_user():
    picture = baker.make(Picture)
    identifications = baker.make(
        PeoplePictureRelation, picture=picture, _quantity=10, _bulk_create=True
    )
    identifications[0].user.is_viewable = False
    identifications[0].user.save()

    assert (
        list(picture.people.viewable_by(old_subscriber_user.make()))
        == identifications[1:]
    )
    assert (
        list(picture.people.viewable_by(baker.make(User, is_superuser=True)))
        == identifications
    )
    assert list(picture.people.viewable_by(identifications[1].user)) == [
        identifications[1]
    ]


class TestDeleteAlbum(TestCase):
    def setUp(cls):
        cls.album: Album = album_recipe.make()
        cls.album_pictures = picture_recipe.make(parent=cls.album, _quantity=5)
        cls.sub_album = album_recipe.make(parent=cls.album)
        cls.sub_album_pictures = picture_recipe.make(parent=cls.sub_album, _quantity=5)

    def test_delete(self):
        album_ids = [self.album.id, self.sub_album.id]
        picture_ids = [
            *[p.id for p in self.album_pictures],
            *[p.id for p in self.sub_album_pictures],
        ]
        self.album.delete()
        # assert not p.exists()
        assert not Album.objects.filter(id__in=album_ids).exists()
        assert not Picture.objects.filter(id__in=picture_ids).exists()
