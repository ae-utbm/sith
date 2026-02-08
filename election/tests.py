from datetime import timedelta

import pytest
from pytest_django.asserts import assertRedirects
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker

from core.baker_recipes import subscriber_user
from core.models import Group, User
from election.models import Candidature, Election, ElectionList, Role, Vote


class TestElection(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.election = Election.objects.first()
        cls.public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
        cls.sli = User.objects.get(username="sli")
        cls.public = baker.make(User)


class TestElectionDetail(TestElection):
    def test_permission_denied(self):
        self.election.view_groups.remove(self.public_group)
        self.client.force_login(self.public)
        response = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        assert response.status_code == 403

    def test_permisson_granted(self):
        self.client.force_login(self.public)
        response = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        assert response.status_code == 200
        assert "La roue tourne" in str(response.content)


class TestElectionUpdateView(TestElection):
    def test_permission_denied(self):
        self.client.force_login(subscriber_user.make())
        response = self.client.get(
            reverse("election:update", args=str(self.election.id))
        )
        assert response.status_code == 403
        response = self.client.post(
            reverse("election:update", args=str(self.election.id))
        )
        assert response.status_code == 403

class TestElectionForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.election = baker.make(
            Election, 
            end_date = now() + timedelta(days=1),
        )
        cls.group = baker.make(Group)
        cls.election.vote_groups.add(cls.group)
        cls.election.edit_groups.add(cls.group)
        lists = baker.make(ElectionList, election=cls.election, _quantity=2, _bulk_create=True)
        cls.roles = baker.make(Role, election=cls.election, _quantity=2, _bulk_create=True)
        users = baker.make(User, _quantity=4, _bulk_create=True)
        cls.cand = [
            baker.make(Candidature, role=cls.roles[0], user=users[0], election_list=lists[0]),
            baker.make(Candidature, role=cls.roles[0], user=users[1], election_list=lists[1]),
            baker.make(Candidature, role=cls.roles[1], user=users[2], election_list=lists[0]),
            baker.make(Candidature, role=cls.roles[1], user=users[3], election_list=lists[1]),
        ]
        cls.url = reverse("election:vote", kwargs={"election_id": cls.election.id})

    def test_election_good_form(self):
        election = self.election
        group = self.group
        roles = self.roles
        cand = self.cand
    
        votes = [
            {
                roles[0].title : "", 
                roles[1].title : str(cand[2].id),
                },

            {
                roles[0].title : "", 
                roles[1].title : "",
                },

            {
                roles[0].title : str(cand[0].id), 
                roles[1].title : str(cand[2].id),
                },

            {
                roles[0].title : str(cand[0].id), 
                roles[1].title : str(cand[3].id),
                },
        ]

        voters = subscriber_user.make(_quantity=len(votes), _bulk_create=True)
        group.users.set(voters)
        
        for voter, vote in zip(voters, votes):
            assert election.can_vote(voter)
            self.client.force_login(voter)
            response = self.client.post(self.url, data = vote)
            assertRedirects(
                response,
                reverse("election:detail", kwargs={"election_id": election.id})
            )
        
        assert set(election.voters.all()) == set(voters)
        assert election.results == {
            roles[0].title: {
                cand[0].user.username: {"percent": 50.0, "vote": 2},
                cand[1].user.username: {"percent": 0.0, "vote": 0},
                "blank vote": {"percent": 50.0, "vote": 2},
                "total vote": 4,
            },
            roles[1].title: {
                cand[2].user.username: {"percent": 50.0, "vote": 2},
                cand[3].user.username: {"percent": 25.0, "vote": 1},
                "blank vote": {"percent": 25.0, "vote": 1},
                "total vote": 4,
            },
        }

    def test_election_bad_form(self):
        election = self.election
        group = self.group
        roles = self.roles
        cand = self.cand
        unknow_user = baker.make(User, _quantity=1, _bulk_create=True)

        votes = [
            {
                roles[0].title : "", 
                roles[1].title : str(cand[0].id), #wrong candidate
                },

            {
                roles[0].title : "",
                },

            {
                roles[0].title : "0123456789", #unknow users
                roles[1].title : str(unknow_user[0].id), #not a candidate
                },

            {
                },
        ]

        voters = subscriber_user.make(_quantity=len(votes), _bulk_create=True)
        group.users.set(voters)

        for voter, vote in zip(voters, votes):
            assert election.can_vote(voter)
            self.client.force_login(voter)
            response = self.client.post(self.url, data = vote)
            assertRedirects(
                response,
                reverse("election:detail", kwargs={"election_id": election.id})
            )

        assert election.results == {
            roles[0].title: {
                cand[0].user.username: {"percent": 0.0, "vote": 0},
                cand[1].user.username: {"percent": 0.0, "vote": 0},
                "blank vote": {"percent": 100.0, "vote": 2},
                "total vote": 2,
            },
            roles[1].title: {
                cand[2].user.username: {"percent": 0.0, "vote": 0},
                cand[3].user.username: {"percent": 0.0, "vote": 0},
                "blank vote": {"percent": 100.0, "vote": 2},
                "total vote": 2,
            },
        }
    
        
@pytest.mark.django_db
def test_election_create_list_permission(client: Client):
    election = baker.make(Election, end_candidature=now() + timedelta(hours=1))
    groups = [
        Group.objects.get(pk=settings.SITH_GROUP_SUBSCRIBERS_ID),
        baker.make(Group),
    ]
    election.candidature_groups.add(groups[0])
    election.edit_groups.add(groups[1])
    url = reverse("election:create_list", kwargs={"election_id": election.id})
    for user in subscriber_user.make(), baker.make(User, groups=[groups[1]]):
        client.force_login(user)
        assert client.get(url).status_code == 200
        # the post is a 200 instead of a 302, because we don't give form data,
        # but we don't care as we only test permissions here
        assert client.post(url).status_code == 200
    client.force_login(baker.make(User))
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403


@pytest.mark.django_db
def test_election_results():
    election = baker.make(
        Election, voters=baker.make(User, _quantity=50, _bulk_create=True)
    )
    lists = baker.make(ElectionList, election=election, _quantity=2, _bulk_create=True)
    roles = baker.make(
        Role, election=election, max_choice=iter([1, 2]), _quantity=2, _bulk_create=True
    )
    users = baker.make(User, _quantity=4, _bulk_create=True)
    cand = [
        baker.make(Candidature, role=roles[0], user=users[0], election_list=lists[0]),
        baker.make(Candidature, role=roles[0], user=users[1], election_list=lists[1]),
        baker.make(Candidature, role=roles[1], user=users[2], election_list=lists[0]),
        baker.make(Candidature, role=roles[1], user=users[3], election_list=lists[1]),
    ]
    votes = [
        baker.make(Vote, role=roles[0], _quantity=20, _bulk_create=True),
        baker.make(Vote, role=roles[0], _quantity=25, _bulk_create=True),
        baker.make(Vote, role=roles[1], _quantity=20, _bulk_create=True),
        baker.make(Vote, role=roles[1], _quantity=35, _bulk_create=True),
        baker.make(Vote, role=roles[1], _quantity=10, _bulk_create=True),
    ]
    cand[0].votes.set(votes[0])
    cand[1].votes.set(votes[1])
    cand[2].votes.set([*votes[2], *votes[4]])
    cand[3].votes.set([*votes[3], *votes[4]])

    assert election.results == {
        roles[0].title: {
            cand[0].user.username: {"percent": 40.0, "vote": 20},
            cand[1].user.username: {"percent": 50.0, "vote": 25},
            "blank vote": {"percent": 10.0, "vote": 5},
            "total vote": 50,
        },
        roles[1].title: {
            cand[2].user.username: {"percent": 30.0, "vote": 30},
            cand[3].user.username: {"percent": 45.0, "vote": 45},
            "blank vote": {"percent": 25.0, "vote": 25},
            "total vote": 100,
        },
    }