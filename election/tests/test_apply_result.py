import itertools
from datetime import timedelta

from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate, now
from model_bakery import baker, seq
from model_bakery.recipe import Recipe
from pytest_django.asserts import assertRedirects

from club.models import Club, ClubRole, Membership
from core.baker_recipes import subscriber_user
from core.models import Group, User
from election.models import Candidature, Election, ElectionList, Role, Vote


class TestApplyResult(TestCase):
    @classmethod
    def setUpTestData(cls):
        # setup is a little bit complicated, but we have to make a whole
        # election to test result application, including the election,
        # the lists, the roles, the candidates and the votes.
        cls.club = baker.make(Club)
        cls.club_roles = baker.make(
            ClubRole,
            club=cls.club,
            is_presidency=iter([True, False, False]),
            is_board=True,
            _quantity=3,
            _bulk_create=True,
        )
        cls.election = baker.make(
            Election,
            clubs=[cls.club],
            edit_groups=[baker.make(Group)],
            end_date=now() - timedelta(minutes=1),
        )
        lists = baker.make(
            ElectionList, election=cls.election, _quantity=2, _bulk_create=True
        )
        role_recipe = Recipe(Role, election=cls.election, title=seq("election role "))
        roles = [
            *role_recipe.make(
                club_role=iter(cls.club_roles), _quantity=len(cls.club_roles)
            ),
            role_recipe.make(),
        ]
        roles[1].max_choice = 2
        roles[1].save()
        cls.candidatures = baker.make(
            Candidature,
            election_list=itertools.chain(
                itertools.repeat(lists[0], len(roles)),
                itertools.repeat(lists[1], len(roles)),
            ),
            role=itertools.cycle(roles),
            user=iter(
                baker.make(
                    User, username=seq("user "), _quantity=len(lists) * len(roles)
                )
            ),
            _quantity=len(lists) * len(roles),
            _bulk_create=True,
        )
        votes = iter(
            baker.make(
                Vote,
                role=itertools.cycle(roles),
                _quantity=6 * len(roles),
                _bulk_create=True,
            )
        )
        through = []
        for cand in cls.candidatures:
            nb_voices = 4 if cand.election_list_id == lists[0].id else 2
            through.extend(
                [
                    Vote.candidature.through(candidature=cand, vote=v)
                    for v in itertools.islice(votes, nb_voices)
                ]
            )
        Vote.candidature.through.objects.bulk_create(through)
        cls.election.voters.set(baker.make(User, _quantity=8, _bulk_create=True))
        cls.url = reverse(
            "election:apply_result", kwargs={"election_id": cls.election.id}
        )

    def test_election_result(self):
        # we have made a complex setup, so testing the results is
        # useful to be sure we didn't make mistake when generating data
        assert self.election.results == {
            "election role 1": {
                "blank vote": {"percent": 25.0, "vote": 2},
                "total vote": 8,
                "user 1": {"percent": 50.0, "vote": 4},
                "user 5": {"percent": 25.0, "vote": 2},
            },
            "election role 2": {
                "blank vote": {"percent": 62.5, "vote": 10},
                "total vote": 16,
                "user 2": {"percent": 25.0, "vote": 4},
                "user 6": {"percent": 12.5, "vote": 2},
            },
            "election role 3": {
                "blank vote": {"percent": 25.0, "vote": 2},
                "total vote": 8,
                "user 3": {"percent": 50.0, "vote": 4},
                "user 7": {"percent": 25.0, "vote": 2},
            },
            "election role 4": {
                "blank vote": {"percent": 25.0, "vote": 2},
                "total vote": 8,
                "user 4": {"percent": 50.0, "vote": 4},
                "user 8": {"percent": 25.0, "vote": 2},
            },
        }

    def test_apply_result(self):
        user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="add_membership")]
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        soup = BeautifulSoup(response.text, "lxml")
        inputs = soup.find_all("input", attrs={"type": "checkbox"})
        assert all("checked" in i.attrs for i in inputs)
        ids = {int(i.attrs["value"]) for i in inputs}
        assert ids == {
            self.candidatures[0].id,
            self.candidatures[1].id,
            self.candidatures[2].id,
            self.candidatures[5].id,
        }
        response = self.client.post(
            self.url, data={"candidates": ids.difference({self.candidatures[5].id})}
        )
        assertRedirects(response, self.url)
        for candidate in self.candidatures[0:3]:
            assert Membership.objects.filter(
                start_date=localdate(),
                end_date=None,
                user=candidate.user,
                role=candidate.role.club_role,
            ).exists()
            assert self.club.members_group.users.contains(candidate.user)
            assert self.club.board_group.users.contains(candidate.user)
        # candidatures[5] was unchecked, so it shouldn't receive a club role
        assert not self.candidatures[5].user.memberships.exists()

        # now that results are applied, it shouldn't be possible to replay the request
        response = self.client.get(self.url)
        assert "Les résultats de cette élection ont été appliqués" in response.text
        response = self.client.post(self.url, data={"candidates": ids})
        assert response.status_code == 403

    def test_no_result_to_apply(self):
        self.election.roles.update(club_role=None)
        user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="add_membership")]
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        soup = BeautifulSoup(response.text, "lxml")
        assert not soup.find("input", attrs={"type": "checkbox"})
        assert "Pas de résultats à appliquer" in response.text

    def test_access_denied(self):
        user = subscriber_user.make()
        self.client.force_login(user)
        response = self.client.get(self.url)
        assert response.status_code == 403
        response = self.client.post(
            self.url, data={"candidates": [self.candidatures[0].id]}
        )
        assert response.status_code == 403

    def test_election_not_finished(self):
        user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="add_membership")]
        )
        self.election.end_date = now() + timedelta(minutes=1)
        self.election.save()
        self.client.force_login(user)
        response = self.client.get(self.url)
        assert response.status_code == 403
        response = self.client.post(
            self.url, data={"candidates": [self.candidatures[0].id]}
        )
        assert response.status_code == 403
