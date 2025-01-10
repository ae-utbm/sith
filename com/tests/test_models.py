import itertools

from django.contrib.auth.models import Permission
from django.test import TestCase
from model_bakery import baker

from com.models import News
from core.models import User


class TestNewsViewableBy(TestCase):
    @classmethod
    def setUpTestData(cls):
        News.objects.all().delete()
        cls.users = baker.make(User, _quantity=3, _bulk_create=True)
        # There are six news and six authors.
        # Each author has one moderated and one non-moderated news
        cls.news = baker.make(
            News,
            author=itertools.cycle(cls.users),
            is_moderated=iter([True, True, True, False, False, False]),
            _quantity=6,
            _bulk_create=True,
        )

    def test_admin_can_view_everything(self):
        """Test with a user that can view non moderated news."""
        user = baker.make(
            User,
            user_permissions=[Permission.objects.get(codename="view_unmoderated_news")],
        )
        assert set(News.objects.viewable_by(user)) == set(self.news)

    def test_normal_user_can_view_moderated_and_self_news(self):
        """Test that basic users can view moderated news and news they authored."""
        user = self.news[0].author
        assert set(News.objects.viewable_by(user)) == {
            self.news[0],
            self.news[1],
            self.news[2],
            self.news[3],
        }
