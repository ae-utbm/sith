# Create your tests here.

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from com.models import News
from core.baker_recipes import subscriber_user
from core.models import User


class TestMatmatronch(TestCase):
    @classmethod
    def setUpTestData(cls):
        News.objects.all().delete()
        User.objects.all().delete()
        users = [
            baker.prepare(User, promo=17),
            baker.prepare(User, promo=17),
            baker.prepare(User, promo=17, department="INFO"),
            baker.prepare(User, promo=18, department="INFO"),
        ]
        cls.users = User.objects.bulk_create(users)
        call_command("update_index", "core", "--remove")

    def test_search(self):
        self.client.force_login(subscriber_user.make())
        response = self.client.get(reverse("matmat:search"))
        assert response.status_code == 200
        response = self.client.get(
            reverse("matmat:search", query={"promo": 17, "department": "INFO"})
        )
        assert response.status_code == 200
        assert list(response.context_data["object_list"]) == [self.users[2]]

    def test_empty_search(self):
        self.client.force_login(subscriber_user.make())
        response = self.client.get(reverse("matmat:search"))
        assert response.status_code == 200
        assert list(response.context_data["object_list"]) == []
        assert not response.context_data["form"].is_valid()

        response = self.client.get(
            reverse(
                "matmat:search",
                query={
                    "promo": "",
                    "role": "",
                    "department": "",
                    "semester": "",
                    "date_of_birth": "",
                },
            )
        )
        assert response.status_code == 200
        assert list(response.context_data["object_list"]) == []
        assert not response.context_data["form"].is_valid()
        assert "Recherche vide" in response.context_data["form"].non_field_errors()
