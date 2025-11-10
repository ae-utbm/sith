from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from core.baker_recipes import subscriber_user
from core.models import User


class TestFetchFamilyApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Relations (A -> B means A is the godchild of B):
        # main_user -> user0 -> user3
        #           -> user1 -> user6 -> user7 -> user8 -> user9
        #           -> user2 -> user10
        #
        # main_user <- user3 <- user11
        #                    <- user12
        #           <- user4 <- user13
        #                    <- user14
        #                    <- user15 <- user16
        #           <- user5

        cls.main_user = baker.make(User)
        cls.users = baker.make(User, _quantity=17, _bulk_create=True)
        cls.main_user.godfathers.add(*cls.users[0:3])
        cls.main_user.godchildren.add(*cls.users[3:6])
        cls.users[1].godfathers.add(cls.users[6])
        cls.users[6].godfathers.add(cls.users[7])
        cls.users[7].godfathers.add(cls.users[8])
        cls.users[8].godfathers.add(cls.users[9])
        cls.users[2].godfathers.add(cls.users[10])

        cls.users[3].godchildren.add(cls.users[11], cls.users[12])
        cls.users[4].godchildren.add(*cls.users[13:16])
        cls.users[15].godchildren.add(cls.users[16])

        cls.root_user = baker.make(User, is_superuser=True)
        cls.subscriber_user = subscriber_user.make()

    def setUp(self):
        self.maxDiff = None

    def test_fetch_family_forbidden(self):
        # Anonymous user
        response = self.client.get(
            reverse("api:family_graph", args=[self.main_user.id])
        )
        assert response.status_code == 401

        self.client.force_login(baker.make(User))  # unsubscribed user
        response = self.client.get(
            reverse("api:family_graph", args=[self.main_user.id])
        )
        assert response.status_code == 403

    def test_fetch_family_hidden_user(self):
        self.main_user.is_subscriber_viewable = False
        self.main_user.save()
        for user_to_login, error_code in [
            (self.main_user, 200),
            (self.subscriber_user, 403),
            (self.root_user, 200),
        ]:
            self.client.force_login(user_to_login)
            response = self.client.get(
                reverse("api:family_graph", args=[self.main_user.id])
            )
            assert response.status_code == error_code

    def test_fetch_family_with_zero_depth(self):
        """Fetch the family with a depth of 0."""
        self.client.force_login(self.main_user)
        response = self.client.get(
            reverse("api:family_graph", args=[self.main_user.id])
            + "?godfathers_depth=0&godchildren_depth=0"
        )
        assert response.status_code == 200
        assert [u["id"] for u in response.json()["users"]] == [self.main_user.id]
        assert response.json()["relationships"] == []

    def test_fetch_empty_family(self):
        empty_user = baker.make(User)
        self.client.force_login(empty_user)
        response = self.client.get(reverse("api:family_graph", args=[empty_user.id]))
        assert response.status_code == 200
        assert [u["id"] for u in response.json()["users"]] == [empty_user.id]
        assert response.json()["relationships"] == []

    def test_fetch_whole_family(self):
        self.client.force_login(self.main_user)
        response = self.client.get(
            reverse("api:family_graph", args=[self.main_user.id])
            + "?godfathers_depth=10&godchildren_depth=10"
        )
        assert response.status_code == 200
        assert [u["id"] for u in response.json()["users"]] == [
            self.main_user.id,
            *[u.id for u in self.users],
        ]
        self.assertCountEqual(
            response.json()["relationships"],
            [
                {"godfather": self.users[0].id, "godchild": self.main_user.id},
                {"godfather": self.users[1].id, "godchild": self.main_user.id},
                {"godfather": self.users[2].id, "godchild": self.main_user.id},
                {"godfather": self.main_user.id, "godchild": self.users[3].id},
                {"godfather": self.main_user.id, "godchild": self.users[4].id},
                {"godfather": self.main_user.id, "godchild": self.users[5].id},
                {"godfather": self.users[6].id, "godchild": self.users[1].id},
                {"godfather": self.users[7].id, "godchild": self.users[6].id},
                {"godfather": self.users[8].id, "godchild": self.users[7].id},
                {"godfather": self.users[9].id, "godchild": self.users[8].id},
                {"godfather": self.users[10].id, "godchild": self.users[2].id},
                {"godfather": self.users[3].id, "godchild": self.users[11].id},
                {"godfather": self.users[3].id, "godchild": self.users[12].id},
                {"godfather": self.users[4].id, "godchild": self.users[13].id},
                {"godfather": self.users[4].id, "godchild": self.users[14].id},
                {"godfather": self.users[4].id, "godchild": self.users[15].id},
                {"godfather": self.users[15].id, "godchild": self.users[16].id},
            ],
        )

    def test_fetch_family_first_level(self):
        """Fetch only the first level of the family."""
        self.client.force_login(self.main_user)
        response = self.client.get(
            reverse("api:family_graph", args=[self.main_user.id])
            + "?godfathers_depth=1&godchildren_depth=1"
        )
        assert response.status_code == 200
        assert [u["id"] for u in response.json()["users"]] == [
            self.main_user.id,
            *[u.id for u in self.users[:6]],
        ]
        self.assertCountEqual(
            response.json()["relationships"],
            [
                {"godfather": self.users[0].id, "godchild": self.main_user.id},
                {"godfather": self.users[1].id, "godchild": self.main_user.id},
                {"godfather": self.users[2].id, "godchild": self.main_user.id},
                {"godfather": self.main_user.id, "godchild": self.users[3].id},
                {"godfather": self.main_user.id, "godchild": self.users[4].id},
                {"godfather": self.main_user.id, "godchild": self.users[5].id},
            ],
        )

    def test_fetch_family_only_godfathers(self):
        """Fetch only the godfathers."""
        self.client.force_login(self.main_user)
        response = self.client.get(
            reverse("api:family_graph", args=[self.main_user.id])
            + "?godfathers_depth=10&godchildren_depth=0"
        )
        assert response.status_code == 200
        assert [u["id"] for u in response.json()["users"]] == [
            self.main_user.id,
            *[u.id for u in self.users[:3]],
            *[u.id for u in self.users[6:11]],
        ]
        self.assertCountEqual(
            response.json()["relationships"],
            [
                {"godfather": self.users[0].id, "godchild": self.main_user.id},
                {"godfather": self.users[1].id, "godchild": self.main_user.id},
                {"godfather": self.users[2].id, "godchild": self.main_user.id},
                {"godfather": self.users[6].id, "godchild": self.users[1].id},
                {"godfather": self.users[7].id, "godchild": self.users[6].id},
                {"godfather": self.users[8].id, "godchild": self.users[7].id},
                {"godfather": self.users[9].id, "godchild": self.users[8].id},
                {"godfather": self.users[10].id, "godchild": self.users[2].id},
            ],
        )

    def test_nb_queries(self):
        # The number of queries should be 1 per level of existing depth.
        with self.assertNumQueries(0):
            self.main_user.get_family(godfathers_depth=0, godchildren_depth=0)
        with self.assertNumQueries(3):
            self.main_user.get_family(godfathers_depth=3, godchildren_depth=0)
        with self.assertNumQueries(3):
            self.main_user.get_family(godfathers_depth=0, godchildren_depth=3)
        with self.assertNumQueries(6):
            self.main_user.get_family(godfathers_depth=3, godchildren_depth=3)
        with self.assertNumQueries(4):
            # If a level is empty, the next ones should not be queried.
            self.main_user.get_family(godfathers_depth=0, godchildren_depth=10)
