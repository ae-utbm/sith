from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from club.models import Membership
from core.baker_recipes import subscriber_user
from core.models import Group, User
from counter.baker_recipes import product_recipe
from counter.forms import CounterEditForm
from counter.models import Counter, CounterSellers


class TestEditCounterSellers(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.counter = baker.make(Counter, type="BAR")
        cls.products = product_recipe.make(_quantity=2, _bulk_create=True)
        cls.counter.products.add(*cls.products)
        users = subscriber_user.make(_quantity=6, _bulk_create=True)
        cls.regular_barmen = users[:2]
        cls.tmp_barmen = users[2:4]
        cls.not_barmen = users[4:]
        CounterSellers.objects.bulk_create(
            [
                *baker.prepare(
                    CounterSellers,
                    counter=cls.counter,
                    user=iter(cls.regular_barmen),
                    is_regular=True,
                    _quantity=len(cls.regular_barmen),
                ),
                *baker.prepare(
                    CounterSellers,
                    counter=cls.counter,
                    user=iter(cls.tmp_barmen),
                    is_regular=False,
                    _quantity=len(cls.tmp_barmen),
                ),
            ]
        )
        cls.operator = baker.make(
            User, groups=[Group.objects.get(id=settings.SITH_GROUP_COUNTER_ADMIN_ID)]
        )

    def test_view_ok(self):
        url = reverse("counter:admin", kwargs={"counter_id": self.counter.id})
        self.client.force_login(self.operator)
        res = self.client.get(url)
        assert res.status_code == 200
        res = self.client.post(
            url,
            data={
                "sellers_regular": [u.id for u in self.regular_barmen],
                "sellers_temporary": [u.id for u in self.tmp_barmen],
                "products": [p.id for p in self.products],
            },
        )
        self.assertRedirects(res, url)

    def test_add_barmen(self):
        form = CounterEditForm(
            data={
                "sellers_regular": [*self.regular_barmen, self.not_barmen[0]],
                "sellers_temporary": [*self.tmp_barmen, self.not_barmen[1]],
                "products": self.products,
            },
            instance=self.counter,
            user=self.operator,
        )
        assert form.is_valid()
        form.save()
        assert set(self.counter.sellers.filter(countersellers__is_regular=True)) == {
            *self.regular_barmen,
            self.not_barmen[0],
        }
        assert set(self.counter.sellers.filter(countersellers__is_regular=False)) == {
            *self.tmp_barmen,
            self.not_barmen[1],
        }

    def test_barman_change_status(self):
        """Test when a barman goes from temporary to regular"""
        form = CounterEditForm(
            data={
                "sellers_regular": [*self.regular_barmen, self.tmp_barmen[0]],
                "sellers_temporary": [*self.tmp_barmen[1:]],
                "products": self.products,
            },
            instance=self.counter,
            user=self.operator,
        )
        assert form.is_valid()
        form.save()
        assert set(self.counter.sellers.filter(countersellers__is_regular=True)) == {
            *self.regular_barmen,
            self.tmp_barmen[0],
        }
        assert set(
            self.counter.sellers.filter(countersellers__is_regular=False)
        ) == set(self.tmp_barmen[1:])

    def test_barman_duplicate(self):
        """Test that a barman cannot be regular and temporary at the same time."""
        form = CounterEditForm(
            data={
                "sellers_regular": [*self.regular_barmen, self.not_barmen[0]],
                "sellers_temporary": [*self.tmp_barmen, self.not_barmen[0]],
                "products": self.products,
            },
            instance=self.counter,
            user=self.operator,
        )
        assert not form.is_valid()
        assert form.errors == {
            "__all__": [
                "Un utilisateur ne peut pas être un barman "
                "régulier et temporaire en même temps, "
                "mais les utilisateurs suivants ont été définis "
                f"comme les deux : {self.not_barmen[0].get_display_name()}"
            ],
        }
        assert set(self.counter.sellers.filter(countersellers__is_regular=True)) == set(
            self.regular_barmen
        )
        assert set(
            self.counter.sellers.filter(countersellers__is_regular=False)
        ) == set(self.tmp_barmen)


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
