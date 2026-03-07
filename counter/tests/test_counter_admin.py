from django.contrib.auth.models import Permission
from django.test import TestCase
from model_bakery import baker

from club.models import Membership
from core.baker_recipes import subscriber_user
from core.models import User
from counter.baker_recipes import product_recipe
from counter.forms import CounterEditForm
from counter.models import Counter


class TestEditCounterProducts(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.counter = baker.make(Counter)
        cls.products = product_recipe.make(_quantity=5, _bulk_create=True)
        cls.counter.products.add(*cls.products)

    def test_admin(self):
        """Test that an admin can add and remove products"""
        user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="change_counter")]
        )
        new_product = product_recipe.make()
        form = CounterEditForm(
            data={"sellers": [], "products": [*self.products[1:], new_product]},
            user=user,
            instance=self.counter,
        )
        assert form.is_valid()
        form.save()
        assert set(self.counter.products.all()) == {*self.products[1:], new_product}

    def test_club_board_id(self):
        """Test that people from counter club board can only add their own products."""
        club = self.counter.club
        user = subscriber_user.make()
        baker.make(Membership, user=user, club=club, end_date=None)
        new_product = product_recipe.make(club=club)
        form = CounterEditForm(
            data={"sellers": [], "products": [*self.products[1:], new_product]},
            user=user,
            instance=self.counter,
        )
        assert form.is_valid()
        form.save()
        assert set(self.counter.products.all()) == {*self.products[1:], new_product}

        new_product = product_recipe.make()  # product not owned by the club
        form = CounterEditForm(
            data={"sellers": [], "products": [*self.products[1:], new_product]},
            user=user,
            instance=self.counter,
        )
        assert not form.is_valid()
        assert form.errors == {
            "products": [
                "Sélectionnez un choix valide. "
                f"{new_product.id} n\u2019en fait pas partie."
            ],
        }
