from io import BytesIO
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.test import TestCase
from model_bakery import baker
from PIL import Image

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import User
from sas.baker_recipes import picture_recipe
from sas.models import PeoplePictureRelation, Picture


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


@pytest.mark.django_db
@pytest.mark.parametrize("save", [True, False])
@pytest.mark.parametrize("initially_saved", [True, False])
@pytest.mark.parametrize("pass_img_kwarg", [True, False])
def test_generate_thumbnail(save, initially_saved, pass_img_kwarg):
    """Test that Picture.generate_thumbnails works properly"""
    image = Image.new("RGB", (2, 1))
    image.putdata([(255, 0, 0), (0, 255, 0)])
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    file = ContentFile(buffer.getvalue(), "img.png")
    picture: Picture = picture_recipe.prepare(
        file=file,
        name=file.name,
        mime_type="image/png",
        _save_related=True,
    )
    if initially_saved:
        picture.save()
    picture.generate_thumbnails(img=image if pass_img_kwarg else None, save=save)
    storage = picture.file.storage
    for f in picture.file, picture.compressed, picture.thumbnail:
        # the tested picture is alone in its album,
        # so there should be a single file in each folder
        assert storage.exists(f.name)
        _dirs, files = storage.listdir(str(Path(f.path).parent))
        assert files == [Path(f.name).name]
    new_img = Image.open(picture.file)
    assert new_img.get_flattened_data() == image.get_flattened_data()
    assert Image.open(picture.thumbnail).size == (200, 100)
    assert Image.open(picture.compressed).size == (1200, 600)
