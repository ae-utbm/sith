from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.models import Club, Membership
from core.baker_recipes import subscriber_user
from core.models import User


class TestSubscriptionPermission(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user: User = subscriber_user.make()
        cls.admin = baker.make(User, is_superuser=True)
        cls.club = baker.make(Club)
        baker.make(Membership, user=cls.user, club=cls.club, role=7)

    def test_give_permission(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("subscription:perms"), {"groups": [self.club.board_group_id]}
        )
        assertRedirects(response, reverse("subscription:perms"))
        assert self.user.has_perm("subscription.add_subscription")

    def test_remove_permission(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("subscription:perms"), {"groups": []})
        assertRedirects(response, reverse("subscription:perms"))
        assert not self.user.has_perm("subscription.add_subscription")

    def test_subscription_page_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("subscription:subscription"))
        assert response.status_code == 403

        self.club.board_group.permissions.add(
            Permission.objects.get(codename="add_subscription")
        )
        response = self.client.get(reverse("subscription:subscription"))
        assert response.status_code == 200
