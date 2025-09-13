from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db.models import Max
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate, localtime, now
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.forms import ClubMemberForm
from club.models import Club, Membership
from club.tests.base import TestClub
from core.baker_recipes import subscriber_user
from core.models import AnonymousUser, User


class TestMembershipQuerySet(TestClub):
    def test_ongoing(self):
        """Test that the ongoing queryset method returns the memberships that
        are not ended.
        """
        current_members = list(self.club.members.ongoing().order_by("id"))
        expected = [
            self.simple_board_member.memberships.get(club=self.club),
            self.president.memberships.get(club=self.club),
            self.richard.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert current_members == expected

    def test_ongoing_with_membership_ending_today(self):
        """Test that a membership ending the present day is considered as ended."""
        today = localdate()
        self.richard.memberships.filter(club=self.club).update(end_date=today)
        current_members = list(self.club.members.ongoing().order_by("id"))
        expected = [
            self.simple_board_member.memberships.get(club=self.club),
            self.president.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert current_members == expected

    def test_board(self):
        """Test that the board queryset method returns the memberships
        of user in the club board.
        """
        board_members = list(self.club.members.board().order_by("id"))
        expected = [
            self.simple_board_member.memberships.get(club=self.club),
            self.president.memberships.get(club=self.club),
            # sli is no more member, but he was in the board
            self.sli.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert board_members == expected

    def test_ongoing_board(self):
        """Test that combining ongoing and board returns users
        who are currently board members of the club.
        """
        members = list(self.club.members.ongoing().board().order_by("id"))
        expected = [
            self.simple_board_member.memberships.get(club=self.club),
            self.president.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert members == expected

    def test_update_invalidate_cache(self):
        """Test that the `update` queryset method properly invalidate cache."""
        mem_skia = self.simple_board_member.memberships.get(club=self.club)
        cache.set(f"membership_{mem_skia.club_id}_{mem_skia.user_id}", mem_skia)
        self.simple_board_member.memberships.update(end_date=localtime(now()).date())
        assert (
            cache.get(f"membership_{mem_skia.club_id}_{mem_skia.user_id}")
            == "not_member"
        )

        mem_richard = self.richard.memberships.get(club=self.club)
        cache.set(
            f"membership_{mem_richard.club_id}_{mem_richard.user_id}", mem_richard
        )
        self.richard.memberships.update(role=5)
        new_mem = self.richard.memberships.get(club=self.club)
        assert new_mem != "not_member"
        assert new_mem.role == 5

    def test_update_change_club_groups(self):
        """Test that `update` set the user groups accordingly."""
        user = baker.make(User)
        membership = baker.make(Membership, end_date=None, user=user, role=5)
        members_group = membership.club.members_group
        board_group = membership.club.board_group
        assert user.groups.contains(members_group)
        assert user.groups.contains(board_group)

        user.memberships.update(role=1)  # from board to simple member
        assert user.groups.contains(members_group)
        assert not user.groups.contains(board_group)

        user.memberships.update(role=5)  # from member to board
        assert user.groups.contains(members_group)
        assert user.groups.contains(board_group)

        user.memberships.update(end_date=localdate())  # end the membership
        assert not user.groups.contains(members_group)
        assert not user.groups.contains(board_group)

    def test_delete_invalidate_cache(self):
        """Test that the `delete` queryset properly invalidate cache."""
        mem_skia = self.simple_board_member.memberships.get(club=self.club)
        mem_comptable = self.president.memberships.get(club=self.club)
        cache.set(f"membership_{mem_skia.club_id}_{mem_skia.user_id}", mem_skia)
        cache.set(
            f"membership_{mem_comptable.club_id}_{mem_comptable.user_id}", mem_comptable
        )

        # should delete the subscriptions of simple_board_member and president
        self.club.members.ongoing().board().delete()

        for membership in (mem_skia, mem_comptable):
            cached_mem = cache.get(
                f"membership_{membership.club_id}_{membership.user_id}"
            )
            assert cached_mem == "not_member"

    def test_delete_remove_from_groups(self):
        """Test that `delete` removes from club groups"""
        user = baker.make(User)
        memberships = baker.make(Membership, role=iter([1, 5]), user=user, _quantity=2)
        club_groups = {
            memberships[0].club.members_group,
            memberships[1].club.members_group,
            memberships[1].club.board_group,
        }
        assert set(user.groups.all()).issuperset(club_groups)
        user.memberships.all().delete()
        assert set(user.groups.all()).isdisjoint(club_groups)


class TestMembershipEditableBy(TestCase):
    @classmethod
    def setUpTestData(cls):
        Membership.objects.all().delete()
        cls.club_a, cls.club_b = baker.make(Club, _quantity=2)
        cls.memberships = [
            *baker.make(
                Membership, role=iter([7, 3, 3, 1]), club=cls.club_a, _quantity=4
            ),
            *baker.make(
                Membership, role=iter([7, 3, 3, 1]), club=cls.club_b, _quantity=4
            ),
        ]

    def test_admin_user(self):
        perm = Permission.objects.get(codename="change_membership")
        user = baker.make(User, user_permissions=[perm])
        qs = Membership.objects.editable_by(user).values_list("id", flat=True)
        assert set(qs) == set(Membership.objects.values_list("id", flat=True))

    def test_simple_subscriber_user(self):
        user = subscriber_user.make()
        assert not Membership.objects.editable_by(user).exists()

    def test_board_member(self):
        # a board member can end lower memberships and its own one
        user = self.memberships[2].user
        qs = Membership.objects.editable_by(user).values_list("id", flat=True)
        expected = {self.memberships[2].id, self.memberships[3].id}
        assert set(qs) == expected


class TestMembership(TestClub):
    def assert_membership_started_today(self, user: User, role: int):
        """Assert that the given membership is active and started today."""
        membership = user.memberships.ongoing().filter(club=self.club).first()
        assert membership is not None
        assert localtime(now()).date() == membership.start_date
        assert membership.end_date is None
        assert membership.role == role
        assert membership.club.get_membership_for(user) == membership
        assert user.is_in_group(pk=self.club.members_group_id)
        assert user.is_in_group(pk=self.club.board_group_id)

    def assert_membership_ended_today(self, user: User):
        """Assert that the given user have a membership which ended today."""
        today = localdate()
        assert user.memberships.filter(club=self.club, end_date=today).exists()
        assert self.club.get_membership_for(user) is None

    def test_access_unauthorized(self):
        """Test that users who never subscribed and anonymous users
        cannot see the page.
        """
        response = self.client.post(self.members_url)
        assertRedirects(
            response, reverse("core:login", query={"next": self.members_url})
        )

        self.client.force_login(self.public)
        response = self.client.post(self.members_url)
        assert response.status_code == 403

    def test_display(self):
        """Test that a GET request return a page where the requested
        information are displayed.
        """
        self.client.force_login(self.simple_board_member)
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.club.id})
        )
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table", id="club_members_table")
        assert [r.text for r in table.find("thead").find_all("td")] == [
            "Utilisateur",
            "Rôle",
            "Description",
            "Depuis",
            "Marquer comme ancien",
        ]
        rows = table.find("tbody").find_all("tr")
        memberships = self.club.members.ongoing().order_by("-role")
        for row, membership in zip(
            rows, memberships.select_related("user"), strict=False
        ):
            user = membership.user
            user_url = reverse("core:user_profile", args=[user.id])
            cols = row.find_all("td")
            user_link = cols[0].find("a")
            assert user_link.attrs["href"] == user_url
            assert user_link.text == user.get_display_name()
            assert cols[1].text == settings.SITH_CLUB_ROLES[membership.role]
            assert cols[2].text == membership.description
            assert cols[3].text == str(membership.start_date)

            if membership.role < 3 or membership.user_id == self.simple_board_member.id:
                # 3 is the role of simple_board_member
                form_input = cols[4].find("input")
                expected_attrs = {
                    "type": "checkbox",
                    "name": "members_old",
                    "value": str(membership.id),
                }
                assert form_input.attrs.items() >= expected_attrs.items()
            else:
                assert cols[4].find_all() == []

    def test_root_add_one_club_member(self):
        """Test that root users can add members to clubs"""
        self.client.force_login(self.root)
        response = self.client.post(
            self.new_members_url, {"user": self.subscriber.id, "role": 3}
        )
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect", "") == reverse(
            "club:club_members", kwargs={"club_id": self.club.id}
        )
        self.subscriber.refresh_from_db()
        self.assert_membership_started_today(self.subscriber, role=3)

    def test_add_unauthorized_members(self):
        """Test that users who are not currently subscribed
        cannot be members of clubs.
        """
        for user in self.public, self.old_subscriber:
            form = ClubMemberForm(
                data={"user": user.id, "role": 1},
                request_user=self.root,
                club=self.club,
            )

            assert not form.is_valid()
            assert form.errors == {
                "user": ["L'utilisateur doit être cotisant pour faire partie d'un club"]
            }

    def test_add_members_already_members(self):
        """Test that users who are already members of a club
        cannot be added again to this club.
        """
        self.client.force_login(self.root)
        current_membership = self.simple_board_member.memberships.ongoing().get(
            club=self.club
        )
        nb_memberships = self.simple_board_member.memberships.count()
        self.client.post(
            self.members_url,
            {"users": self.simple_board_member.id, "role": current_membership.role + 1},
        )
        self.simple_board_member.refresh_from_db()
        assert nb_memberships == self.simple_board_member.memberships.count()
        new_membership = self.simple_board_member.memberships.ongoing().get(
            club=self.club
        )
        assert current_membership == new_membership
        assert self.club.get_membership_for(self.simple_board_member) == new_membership

    def test_add_not_existing_users(self):
        """Test that not existing users cannot be added in clubs.
        If one user in the request is invalid, no membership creation at all
        can take place.
        """
        nb_memberships = self.club.members.count()
        max_id = User.objects.aggregate(id=Max("id"))["id"]
        for members in [max_id + 1], [max_id + 1, self.subscriber.id]:
            form = ClubMemberForm(
                data={"user": members, "role": 1},
                request_user=self.root,
                club=self.club,
            )
            assert not form.is_valid()
            assert form.errors == {
                "user": [
                    "Sélectionnez un choix valide. "
                    "Ce choix ne fait pas partie de ceux disponibles."
                ]
            }
        self.club.refresh_from_db()
        assert self.club.members.count() == nb_memberships

    def test_president_add_members(self):
        """Test that the president of the club can add members."""
        president = self.club.members.get(role=10).user
        nb_club_membership = self.club.members.count()
        nb_subscriber_memberships = self.subscriber.memberships.count()
        self.client.force_login(president)
        response = self.client.post(
            self.new_members_url, {"user": self.subscriber.id, "role": 9}
        )
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect", "") == reverse(
            "club:club_members", kwargs={"club_id": self.club.id}
        )
        self.club.refresh_from_db()
        self.subscriber.refresh_from_db()
        assert self.club.members.count() == nb_club_membership + 1
        assert self.subscriber.memberships.count() == nb_subscriber_memberships + 1
        self.assert_membership_started_today(self.subscriber, role=9)

    def test_add_member_greater_role(self):
        """Test that a member of the club member cannot create
        a membership with a greater role than its own.
        """
        form = ClubMemberForm(
            data={"user": self.subscriber.id, "role": 10},
            request_user=self.simple_board_member,
            club=self.club,
        )
        nb_memberships = self.club.members.count()

        assert not form.is_valid()
        assert form.errors == {
            "role": ["Sélectionnez un choix valide. 10 n\u2019en fait pas partie."]
        }
        self.club.refresh_from_db()
        assert nb_memberships == self.club.members.count()
        assert not self.subscriber.memberships.filter(club=self.club).exists()

    def test_add_member_without_role(self):
        """Test that trying to add members without specifying their role fails."""
        form = ClubMemberForm(
            data={"user": self.subscriber.id}, request_user=self.root, club=self.club
        )

        assert not form.is_valid()
        assert form.errors == {"role": ["Ce champ est obligatoire."]}

    def test_end_membership_self(self):
        """Test that a member can end its own membership."""
        self.client.force_login(self.simple_board_member)
        membership = self.club.members.get(end_date=None, user=self.simple_board_member)
        self.client.post(self.members_url, {"members_old": [membership.id]})
        self.simple_board_member.refresh_from_db()
        self.assert_membership_ended_today(self.simple_board_member)

    def test_end_membership_lower_role(self):
        """Test that board members of the club can end memberships
        of users with lower roles.
        """
        # reminder : simple_board_member has role 3
        self.client.force_login(self.simple_board_member)
        membership = baker.make(Membership, club=self.club, role=2, end_date=None)
        response = self.client.post(self.members_url, {"members_old": [membership.id]})
        self.assertRedirects(response, self.members_url)
        self.club.refresh_from_db()
        self.assert_membership_ended_today(membership.user)

    def test_end_membership_higher_role(self):
        """Test that board members of the club cannot end memberships
        of users with higher roles.
        """
        membership = self.president.memberships.filter(club=self.club).first()
        self.client.force_login(self.simple_board_member)
        self.client.post(self.members_url, {"members_old": [membership.id]})
        self.club.refresh_from_db()
        new_membership = self.club.get_membership_for(self.president)
        assert new_membership is not None
        assert new_membership == membership

        membership.refresh_from_db()
        assert membership.end_date is None

    def test_end_membership_with_permission(self):
        """Test that users with permission can end any membership."""
        # make subscriber a board member
        nb_memberships = self.club.members.ongoing().count()
        self.client.force_login(
            subscriber_user.make(
                user_permissions=[Permission.objects.get(codename="change_membership")]
            )
        )
        president_membership = self.club.president
        response = self.client.post(
            self.members_url, {"members_old": [president_membership.id]}
        )
        self.assertRedirects(response, self.members_url)
        self.assert_membership_ended_today(president_membership.user)
        assert self.club.members.ongoing().count() == nb_memberships - 1

    def test_end_membership_as_foreigner(self):
        """Test that users who are not in this club cannot end its memberships."""
        nb_memberships = self.club.members.count()
        membership = self.richard.memberships.filter(club=self.club).first()
        self.client.force_login(self.subscriber)
        self.client.post(self.members_url, {"members_old": [self.richard.id]})
        # nothing should have changed
        membership.refresh_from_db()
        assert self.club.members.count() == nb_memberships
        assert membership.end_date is None

    def test_remove_from_club_group(self):
        """Test that when a membership ends, the user is removed from club groups."""
        user = baker.make(User)
        baker.make(Membership, user=user, club=self.club, end_date=None, role=3)
        assert user.groups.contains(self.club.members_group)
        assert user.groups.contains(self.club.board_group)
        user.memberships.update(end_date=localdate())
        assert not user.groups.contains(self.club.members_group)
        assert not user.groups.contains(self.club.board_group)

    def test_add_to_club_group(self):
        """Test that when a membership begins, the user is added to the club group."""
        assert not self.subscriber.groups.contains(self.club.members_group)
        assert not self.subscriber.groups.contains(self.club.board_group)
        baker.make(Membership, club=self.club, user=self.subscriber, role=3)
        assert self.subscriber.groups.contains(self.club.members_group)
        assert self.subscriber.groups.contains(self.club.board_group)

    def test_change_position_in_club(self):
        """Test that when moving from board to members, club group change"""
        membership = baker.make(
            Membership, club=self.club, user=self.subscriber, role=3
        )
        assert self.subscriber.groups.contains(self.club.members_group)
        assert self.subscriber.groups.contains(self.club.board_group)
        membership.role = 1
        membership.save()
        assert self.subscriber.groups.contains(self.club.members_group)
        assert not self.subscriber.groups.contains(self.club.board_group)

    def test_club_owner(self):
        """Test that a club is owned only by board members of the main club."""
        anonymous = AnonymousUser()
        assert not self.club.is_owned_by(anonymous)
        assert not self.club.is_owned_by(self.subscriber)

        # make sli a board member
        self.sli.memberships.all().delete()
        Membership(club=self.ae, user=self.sli, role=3).save()
        assert self.club.is_owned_by(self.sli)

    def test_change_club_name(self):
        """Test that changing the club name doesn't break things."""
        members_group = self.club.members_group
        board_group = self.club.board_group
        initial_members = set(members_group.users.values_list("id", flat=True))
        initial_board = set(board_group.users.values_list("id", flat=True))
        self.club.name = "something else"
        self.club.save()
        self.club.refresh_from_db()

        # The names should have changed, but not the ids nor the group members
        assert self.club.members_group.name == "something else - Membres"
        assert self.club.board_group.name == "something else - Bureau"
        assert self.club.members_group.id == members_group.id
        assert self.club.board_group.id == board_group.id
        new_members = set(self.club.members_group.users.values_list("id", flat=True))
        new_board = set(self.club.board_group.users.values_list("id", flat=True))
        assert new_members == initial_members
        assert new_board == initial_board
