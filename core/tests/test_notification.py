from datetime import timedelta
from operator import attrgetter

import pytest
from bs4 import BeautifulSoup
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker, seq
from pytest_django.asserts import assertRedirects

from core.baker_recipes import subscriber_user
from core.models import Notification


@pytest.mark.django_db
class TestNotificationList(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = subscriber_user.make()
        url = reverse("core:user_profile", kwargs={"user_id": cls.user.id})
        cls.notifs = baker.make(
            Notification,
            user=cls.user,
            url=url,
            viewed=False,
            date=seq(now() - timedelta(days=1), timedelta(hours=1)),
            _quantity=10,
            _bulk_create=True,
        )

    def test_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:notification_list"))
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, "lxml")
        ul = soup.find("ul", id="notifications")
        elements = list(ul.find_all("li"))
        assert len(elements) == len(self.notifs)
        notifs = sorted(self.notifs, key=attrgetter("date"), reverse=True)
        for element, notif in zip(elements, notifs, strict=True):
            assert element.find("a")["href"] == reverse(
                "core:notification", kwargs={"notif_id": notif.id}
            )

    def test_read_all(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("core:notification_list", query={"read_all": None})
        )
        assert response.status_code == 200
        assert not self.user.notifications.filter(viewed=True).exists()


@pytest.mark.django_db
def test_notification_redirect(client: Client):
    user = subscriber_user.make()
    url = reverse("core:user_profile", kwargs={"user_id": user.id})
    notif = baker.make(Notification, user=user, url=url, viewed=False)
    client.force_login(user)
    response = client.get(reverse("core:notification", kwargs={"notif_id": notif.id}))
    assertRedirects(response, url)
    notif.refresh_from_db()
    assert notif.viewed is True
