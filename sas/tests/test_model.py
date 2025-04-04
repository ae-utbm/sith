from django.test import TestCase
from model_bakery import baker

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import User
from sas.baker_recipes import picture_recipe
from sas.models import Picture


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
