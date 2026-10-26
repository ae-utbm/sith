from datetime import datetime

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from model_bakery import baker

from club.models import Club
from club.views import ClubNewsView
from com.models import News, NewsDate
from core.baker_recipes import subscriber_user
from core.models import User


class TestClubNews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.club = baker.make(Club)
        cls.news = baker.make(
            News, club=cls.club, is_published=True, author=baker.make(User), _quantity=5
        )
        d = datetime(year=2025, month=10, day=1, tzinfo=get_current_timezone())
        dates = [
            baker.prepare(NewsDate, news=cls.news[0], start_date=d),
            baker.prepare(NewsDate, news=cls.news[0], start_date=d.replace(day=8)),
            baker.prepare(NewsDate, news=cls.news[0], start_date=d.replace(day=15)),
            baker.prepare(NewsDate, news=cls.news[1], start_date=d.replace(month=5)),
            baker.prepare(NewsDate, news=cls.news[2], start_date=d.replace(month=4)),
            baker.prepare(NewsDate, news=cls.news[3], start_date=d.replace(year=2024)),
            baker.prepare(NewsDate, news=cls.news[4], start_date=d.replace(year=2020)),
        ]
        NewsDate.objects.bulk_create(dates)
        cls.url = reverse("club:news_list", kwargs={"club_id": cls.club.id})

    def test_load_page(self):
        """Just test that the page loads."""
        self.client.force_login(subscriber_user.make())
        res = self.client.get(self.url)
        assert res.status_code == 200

    def test_page_data(self):
        """Test that we display the good events."""
        # For this test, the object we want to test
        # is built with `itertools.groupby`.
        # However, it is consumed when rendering the template,
        # making it unusable for later testing purposes,
        # so we must use lower level django APIs in this test.
        request = RequestFactory().get(self.url)
        request.user = subscriber_user.make()
        response = ClubNewsView.as_view()(request, club_id=self.club.id)
        events = [
            (semester_code, list(dates))
            for semester_code, dates in response.context_data["events"]
        ]
        assert events == [
            ("A25", [self.news[0]]),
            ("P25", [self.news[1], self.news[2]]),
            ("A24", [self.news[3]]),
            ("A20", [self.news[4]]),
        ]
