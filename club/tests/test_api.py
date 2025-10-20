from django.test import Client, TestCase
from django.urls import reverse

from core.models import User


class TestClubSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:search_club")
        cls.client = Client()
        cls.user = User.objects.get(username="root")

    def test_inactive_club(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"is_active": False})
        assert response.status_code == 200

        data = response.json()
        names = [item["name"] for item in data["results"]]
        assert "AE" not in names
        assert "Troll Penché" not in names

    def test_excluded_id(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"exclude_ids": [1]})
        assert response.status_code == 200

        data = response.json()
        names = [item["name"] for item in data["results"]]
        assert "AE" not in names

    def test_club_search(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"search": "AE"})
        assert response.status_code == 200

        data = response.json()
        names = [item["name"] for item in data["results"]]
        assert len(names) > 1

    def test_anonymous_user_unauthorized(self):
        response = self.client.get(self.url)
        assert response.status_code == 401
