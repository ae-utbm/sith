# -*- coding:utf-8 -*
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.utils.translation import gettext as _

from club.forms import MailingForm
from club.models import Club, Mailing, Membership
from core.models import AnonymousUser, User
from sith.settings import SITH_BAR_MANAGER, SITH_MAIN_CLUB_ID


class ClubTest(TestCase):
    """
    Set up data for test cases related to clubs and membership
    The generated dataset is the one created by the populate command,
    plus the following modifications :

    - `self.club` is a dummy club recreated for each test
    - `self.club` has two board members : skia (role 3) and comptable (role 10)
    - `self.club` has one regular member : richard
    - `self.club` has one former member : sli (who had role 2)
    - None of the `self.club` members are in the AE club.
    """

    @classmethod
    def setUpTestData(cls):
        # subscribed users - initial members
        cls.skia = User.objects.get(username="skia")
        # by default, Skia is in the AE, which creates side effect
        cls.skia.memberships.all().delete()
        cls.richard = User.objects.get(username="rbatsbak")
        cls.comptable = User.objects.get(username="comptable")
        cls.sli = User.objects.get(username="sli")
        cls.root = User.objects.get(username="root")

        # subscribed users - not initial members
        cls.krophil = User.objects.get(username="krophil")
        cls.subscriber = User.objects.get(username="subscriber")

        # old subscriber
        cls.old_subscriber = User.objects.get(username="old_subscriber")

        # not subscribed
        cls.public = User.objects.get(username="public")

        cls.ae = Club.objects.filter(pk=SITH_MAIN_CLUB_ID)[0]
        cls.club = Club.objects.create(
            name="Fake Club",
            unix_name="fake-club",
            address="5 rue de la République, 90000 Belfort",
        )
        cls.members_url = reverse(
            "club:club_members", kwargs={"club_id": cls.club.id}
        )
        a_month_ago = now() - timedelta(days=30)
        yesterday = now() - timedelta(days=1)
        Membership.objects.create(
            club=cls.club, user=cls.skia, start_date=a_month_ago, role=3
        )
        Membership.objects.create(club=cls.club, user=cls.richard, role=1)
        Membership.objects.create(
            club=cls.club, user=cls.comptable, start_date=a_month_ago, role=10
        )

        # sli was a member but isn't anymore
        Membership.objects.create(
            club=cls.club,
            user=cls.sli,
            start_date=a_month_ago,
            end_date=yesterday,
            role=2,
        )

    def setUp(self):
        cache.clear()


class MembershipQuerySetTest(ClubTest):
    def test_ongoing(self):
        """
        Test that the ongoing queryset method returns the memberships that
        are not ended.
        """
        current_members = list(self.club.members.ongoing().order_by("id"))
        expected = [
            self.skia.memberships.get(club=self.club),
            self.comptable.memberships.get(club=self.club),
            self.richard.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert current_members == expected

    def test_board(self):
        """
        Test that the board queryset method returns the memberships
        of user in the club board
        """
        board_members = list(self.club.members.board().order_by("id"))
        expected = [
            self.skia.memberships.get(club=self.club),
            self.comptable.memberships.get(club=self.club),
            # sli is no more member, but he was in the board
            self.sli.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert board_members == expected

    def test_ongoing_board(self):
        """
        Test that combining ongoing and board returns users
        who are currently board members of the club
        """
        members = list(self.club.members.ongoing().board().order_by("id"))
        expected = [
            self.skia.memberships.get(club=self.club),
            self.comptable.memberships.get(club=self.club),
        ]
        expected.sort(key=lambda i: i.id)
        assert members == expected

    def test_update_invalidate_cache(self):
        """
        Test that the `update` queryset method properly invalidate cache
        """
        mem_skia = self.skia.memberships.get(club=self.club)
        cache.set(f"membership_{mem_skia.club_id}_{mem_skia.user_id}", mem_skia)
        self.skia.memberships.update(end_date=localtime(now()).date())
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

    def test_delete_invalidate_cache(self):
        """
        Test that the `delete` queryset properly invalidate cache
        """

        mem_skia = self.skia.memberships.get(club=self.club)
        mem_comptable = self.comptable.memberships.get(club=self.club)
        cache.set(f"membership_{mem_skia.club_id}_{mem_skia.user_id}", mem_skia)
        cache.set(
            f"membership_{mem_comptable.club_id}_{mem_comptable.user_id}", mem_comptable
        )

        # should delete the subscriptions of skia and comptable
        self.club.members.ongoing().board().delete()

        assert (
            cache.get(f"membership_{mem_skia.club_id}_{mem_skia.user_id}")
            == "not_member"
        )
        assert (
            cache.get(f"membership_{mem_comptable.club_id}_{mem_comptable.user_id}")
            == "not_member",
        )


class ClubModelTest(ClubTest):
    def assert_membership_started_today(self, user: User, role: int):
        """
        Assert that the given membership is active and started today
        """
        membership = user.memberships.ongoing().filter(club=self.club).first()
        assert membership is not None
        assert localtime(now()).date() == membership.start_date
        assert membership.end_date is None
        assert membership.role == role
        assert membership.club.get_membership_for(user) == membership
        member_group = self.club.unix_name + settings.SITH_MEMBER_SUFFIX
        board_group = self.club.unix_name + settings.SITH_BOARD_SUFFIX
        assert user.is_in_group(name=member_group)
        assert user.is_in_group(name=board_group)

    def assert_membership_ended_today(self, user: User):
        """
        Assert that the given user have a membership which ended today
        """
        today = localtime(now()).date()
        assert user.memberships.filter(club=self.club, end_date=today).exists()
        assert self.club.get_membership_for(user) is None

    def test_access_unauthorized(self):
        """
        Test that users who never subscribed and anonymous users
        cannot see the page
        """
        response = self.client.post(self.members_url)
        assert response.status_code == 403

        self.client.force_login(self.public)
        response = self.client.post(self.members_url)
        assert response.status_code == 403

    def test_display(self):
        """
        Test that a GET request return a page where the requested
        information are displayed.
        """
        self.client.force_login(self.skia)
        response = self.client.get(self.members_url)
        assert response.status_code == 200
        expected_html = (
            "<table><thead><tr>"
            "<td>Utilisateur</td><td>Rôle</td><td>Description</td>"
            "<td>Depuis</td><td>Marquer comme ancien</td>"
            "</tr></thead><tbody>"
        )
        memberships = self.club.members.ongoing().order_by("-role")
        input_id = 0
        for membership in memberships.select_related("user"):
            user = membership.user
            expected_html += (
                f"<tr><td><a href=\"{reverse('core:user_profile', args=[user.id])}\">"
                f"{user.get_display_name()}</a></td>"
                f"<td>{settings.SITH_CLUB_ROLES[membership.role]}</td>"
                f"<td>{membership.description}</td>"
                f"<td>{membership.start_date}</td><td>"
            )
            if membership.role <= 3:  # 3 is the role of skia
                expected_html += (
                    '<input type="checkbox" name="users_old" '
                    f'value="{user.id}" '
                    f'id="id_users_old_{input_id}">'
                )
                input_id += 1
            expected_html += "</td></tr>"
        expected_html += "</tbody></table>"
        self.assertInHTML(expected_html, response.content.decode())

    def test_root_add_one_club_member(self):
        """
        Test that root users can add members to clubs, one at a time
        """
        self.client.force_login(self.root)
        response = self.client.post(
            self.members_url,
            {"users": self.subscriber.id, "role": 3},
        )
        self.assertRedirects(response, self.members_url)
        self.subscriber.refresh_from_db()
        self.assert_membership_started_today(self.subscriber, role=3)

    def test_root_add_multiple_club_member(self):
        """
        Test that root users can add multiple members at once to clubs
        """
        self.client.force_login(self.root)
        response = self.client.post(
            self.members_url,
            {
                "users": f"|{self.subscriber.id}|{self.krophil.id}|",
                "role": 3,
            },
        )
        self.assertRedirects(response, self.members_url)
        self.subscriber.refresh_from_db()
        self.assert_membership_started_today(self.subscriber, role=3)
        self.assert_membership_started_today(self.krophil, role=3)

    def test_add_unauthorized_members(self):
        """
        Test that users who are not currently subscribed
        cannot be members of clubs.
        """
        self.client.force_login(self.root)
        response = self.client.post(
            self.members_url,
            {"users": self.public.id, "role": 1},
        )
        assert not self.public.memberships.filter(club=self.club).exists()
        assert '<ul class="errorlist"><li>' in response.content.decode()

        response = self.client.post(
            self.members_url,
            {"users": self.old_subscriber.id, "role": 1},
        )
        assert not self.public.memberships.filter(club=self.club).exists()
        assert self.club.get_membership_for(self.public) is None
        assert '<ul class="errorlist"><li>' in response.content.decode()

    def test_add_members_already_members(self):
        """
        Test that users who are already members of a club
        cannot be added again to this club
        """
        self.client.force_login(self.root)
        current_membership = self.skia.memberships.ongoing().get(club=self.club)
        nb_memberships = self.skia.memberships.count()
        self.client.post(
            self.members_url,
            {"users": self.skia.id, "role": current_membership.role + 1},
        )
        self.skia.refresh_from_db()
        assert nb_memberships == self.skia.memberships.count()
        new_membership = self.skia.memberships.ongoing().get(club=self.club)
        assert current_membership == new_membership
        assert self.club.get_membership_for(self.skia) == new_membership

    def test_add_not_existing_users(self):
        """
        Test that not existing users cannot be added in clubs.
        If one user in the request is invalid, no membership creation at all
        can take place.
        """
        self.client.force_login(self.root)
        nb_memberships = self.club.members.count()
        response = self.client.post(
            self.members_url,
            {"users": [9999], "role": 1},
        )
        assert response.status_code == 200
        assert '<ul class="errorlist"><li>' in response.content.decode()
        self.club.refresh_from_db()
        assert self.club.members.count() == nb_memberships
        response = self.client.post(
            self.members_url,
            {
                "users": f"|{self.subscriber.id}|{9999}|",
                "start_date": "12/06/2016",
                "role": 3,
            },
        )
        assert response.status_code == 200
        assert '<ul class="errorlist"><li>' in response.content.decode()
        self.club.refresh_from_db()
        assert self.club.members.count() == nb_memberships

    def test_president_add_members(self):
        """
        Test that the president of the club can add members
        """
        president = self.club.members.get(role=10).user
        nb_club_membership = self.club.members.count()
        nb_subscriber_memberships = self.subscriber.memberships.count()
        self.client.force_login(president)
        response = self.client.post(
            self.members_url,
            {"users": self.subscriber.id, "role": 9},
        )
        self.assertRedirects(response, self.members_url)
        self.club.refresh_from_db()
        self.subscriber.refresh_from_db()
        assert self.club.members.count() == nb_club_membership + 1
        assert self.subscriber.memberships.count() == nb_subscriber_memberships + 1
        self.assert_membership_started_today(self.subscriber, role=9)

    def test_add_member_greater_role(self):
        """
        Test that a member of the club member cannot create
        a membership with a greater role than its own.
        """
        self.client.force_login(self.skia)
        nb_memberships = self.club.members.count()
        response = self.client.post(
            self.members_url,
            {"users": self.subscriber.id, "role": 10},
        )
        assert response.status_code == 200
        self.assertInHTML(
            "<li>Vous n'avez pas la permission de faire cela</li>",
            response.content.decode(),
        )
        self.club.refresh_from_db()
        assert nb_memberships == self.club.members.count()
        assert not self.subscriber.memberships.filter(club=self.club).exists()

    def test_add_member_without_role(self):
        """
        Test that trying to add members without specifying their role fails
        """
        self.client.force_login(self.root)
        response = self.client.post(
            self.members_url,
            {"users": self.subscriber.id, "start_date": "12/06/2016"},
        )
        assert (
            '<ul class="errorlist"><li>Vous devez choisir un r'
            in response.content.decode()
        )

    def test_end_membership_self(self):
        """
        Test that a member can end its own membership
        """
        self.client.force_login(self.skia)
        self.client.post(
            self.members_url,
            {"users_old": self.skia.id},
        )
        self.skia.refresh_from_db()
        self.assert_membership_ended_today(self.skia)

    def test_end_membership_lower_role(self):
        """
        Test that board members of the club can end memberships
        of users with lower roles
        """
        # remainder : skia has role 3, comptable has role 10, richard has role 1
        self.client.force_login(self.skia)
        response = self.client.post(
            self.members_url,
            {"users_old": self.richard.id},
        )
        self.assertRedirects(response, self.members_url)
        self.club.refresh_from_db()
        self.assert_membership_ended_today(self.richard)

    def test_end_membership_higher_role(self):
        """
        Test that board members of the club cannot end memberships
        of users with higher roles
        """
        membership = self.comptable.memberships.filter(club=self.club).first()
        self.client.force_login(self.skia)
        self.client.post(
            self.members_url,
            {"users_old": self.comptable.id},
        )
        self.club.refresh_from_db()
        new_membership = self.club.get_membership_for(self.comptable)
        assert new_membership is not None
        assert new_membership == membership

        membership = self.comptable.memberships.filter(club=self.club).first()
        assert membership.end_date is None

    def test_end_membership_as_main_club_board(self):
        """
        Test that board members of the main club can end the membership
        of anyone
        """
        # make subscriber a board member
        self.subscriber.memberships.all().delete()
        Membership.objects.create(club=self.ae, user=self.subscriber, role=3)

        nb_memberships = self.club.members.count()
        self.client.force_login(self.subscriber)
        response = self.client.post(
            self.members_url,
            {"users_old": self.comptable.id},
        )
        self.assertRedirects(response, self.members_url)
        self.assert_membership_ended_today(self.comptable)
        assert self.club.members.ongoing().count() == nb_memberships - 1

    def test_end_membership_as_root(self):
        """
        Test that root users can end the membership of anyone
        """
        nb_memberships = self.club.members.count()
        self.client.force_login(self.root)
        response = self.client.post(
            self.members_url,
            {"users_old": [self.comptable.id]},
        )
        self.assertRedirects(response, self.members_url)
        self.assert_membership_ended_today(self.comptable)
        assert self.club.members.ongoing().count() == nb_memberships - 1
        assert self.club.members.count() == nb_memberships

    def test_end_membership_as_foreigner(self):
        """
        Test that users who are not in this club cannot end its memberships
        """
        nb_memberships = self.club.members.count()
        membership = self.richard.memberships.filter(club=self.club).first()
        self.client.force_login(self.subscriber)
        self.client.post(
            self.members_url,
            {"users_old": [self.richard.id]},
        )
        # nothing should have changed
        new_mem = self.club.get_membership_for(self.richard)
        assert self.club.members.count() == nb_memberships
        assert membership == new_mem

    def test_delete_remove_from_meta_group(self):
        """
        Test that when a club is deleted, all its members are removed from the
        associated metagroup
        """
        memberships = self.club.members.select_related("user")
        users = [membership.user for membership in memberships]
        meta_group = self.club.unix_name + settings.SITH_MEMBER_SUFFIX

        self.club.delete()
        for user in users:
            assert not user.is_in_group(name=meta_group)

    def test_add_to_meta_group(self):
        """
        Test that when a membership begins, the user is added to the meta group
        """
        group_members = self.club.unix_name + settings.SITH_MEMBER_SUFFIX
        board_members = self.club.unix_name + settings.SITH_BOARD_SUFFIX
        assert not self.subscriber.is_in_group(name=group_members)
        assert not self.subscriber.is_in_group(name=board_members)
        Membership.objects.create(club=self.club, user=self.subscriber, role=3)
        assert self.subscriber.is_in_group(name=group_members)
        assert self.subscriber.is_in_group(name=board_members)

    def test_remove_from_meta_group(self):
        """
        Test that when a membership ends, the user is removed from meta group
        """
        group_members = self.club.unix_name + settings.SITH_MEMBER_SUFFIX
        board_members = self.club.unix_name + settings.SITH_BOARD_SUFFIX
        assert self.comptable.is_in_group(name=group_members)
        assert self.comptable.is_in_group(name=board_members)
        self.comptable.memberships.update(end_date=localtime(now()))
        assert not self.comptable.is_in_group(name=group_members)
        assert not self.comptable.is_in_group(name=board_members)

    def test_club_owner(self):
        """
        Test that a club is owned only by board members of the main club
        """
        anonymous = AnonymousUser()
        assert not self.club.is_owned_by(anonymous)
        assert not self.club.is_owned_by(self.subscriber)

        # make sli a board member
        self.sli.memberships.all().delete()
        Membership(club=self.ae, user=self.sli, role=3).save()
        assert self.club.is_owned_by(self.sli)


class MailingFormTest(TestCase):
    """Perform validation tests for MailingForm"""

    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.get(username="skia")
        cls.rbatsbak = User.objects.get(username="rbatsbak")
        cls.krophil = User.objects.get(username="krophil")
        cls.comunity = User.objects.get(username="comunity")
        cls.root = User.objects.get(username="root")
        cls.bdf = Club.objects.get(unix_name=SITH_BAR_MANAGER["unix_name"])
        cls.mail_url = reverse("club:mailing", kwargs={"club_id": cls.bdf.id})

    def setUp(self):
        Membership(
            user=self.rbatsbak,
            club=self.bdf,
            start_date=timezone.now(),
            role=settings.SITH_CLUB_ROLES_ID["Board member"],
        ).save()

    def test_mailing_list_add_no_moderation(self):
        # Test with Communication admin
        self.client.force_login(self.comunity)
        response = self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "foyer"},
        )
        self.assertRedirects(response, self.mail_url)
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "Liste de diffusion foyer@utbm.fr" in response.content.decode()

        # Test with Root
        self.client.force_login(self.root)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "Liste de diffusion mde@utbm.fr" in response.content.decode()

    def test_mailing_list_add_moderation(self):
        self.client.force_login(self.rbatsbak)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Liste de diffusion mde@utbm.fr" not in content
        assert "<p>Listes de diffusions en attente de modération</p>" in content
        assert "<li>mde@utbm.fr" in content

    def test_mailing_list_forbidden(self):
        # With anonymous user
        response = self.client.get(self.mail_url)
        self.assertContains(response, "", status_code=403)

        # With user not in club
        self.client.force_login(self.krophil)
        response = self.client.get(self.mail_url)
        assert response.status_code == 403

    def test_add_new_subscription_fail_not_moderated(self):
        self.client.force_login(self.rbatsbak)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.skia.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "skia@git.an" not in response.content.decode()

    def test_add_new_subscription_success(self):
        # Prepare mailing list
        self.client.force_login(self.comunity)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        # Add single user
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.skia.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "skia@git.an" in response.content.decode()

        # Add multiple users
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": "|%s|%s|" % (self.comunity.id, self.rbatsbak.id),
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "richard@git.an" in content
        assert "comunity@git.an" in content
        assert "skia@git.an" in content

        # Add arbitrary email
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_email": "arbitrary@git.an",
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "richard@git.an" in content
        assert "comunity@git.an" in content
        assert "skia@git.an" in content
        assert "arbitrary@git.an" in content

        # Add user and arbitrary email
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_email": "more.arbitrary@git.an",
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "richard@git.an" in content
        assert "comunity@git.an" in content
        assert "skia@git.an" in content
        assert "arbitrary@git.an" in content
        assert "more.arbitrary@git.an" in content
        assert "krophil@git.an" in content

    def test_add_new_subscription_fail_form_errors(self):
        # Prepare mailing list
        self.client.force_login(self.comunity)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        # Neither email or email is specified
        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code
        self.assertInHTML(
            _("You must specify at least an user or an email address"),
            response.content.decode(),
        )

        # No mailing specified
        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
            },
        )
        assert response.status_code == 200
        assert _("This field is required") in response.content.decode()

        # One of the selected users doesn't exist
        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": "|789|",
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code == 200
        self.assertInHTML(
            _("One of the selected users doesn't exist"), response.content.decode()
        )

        # An user has no email adress
        self.krophil.email = ""
        self.krophil.save()

        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code == 200
        self.assertInHTML(
            _("One of the selected users doesn't have an email address"),
            response.content.decode(),
        )

        self.krophil.email = "krophil@git.an"
        self.krophil.save()

        # An user is added twice

        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )

        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code == 200
        self.assertInHTML(
            _("This email is already suscribed in this mailing"),
            response.content.decode(),
        )

    def test_remove_subscription_success(self):
        # Prepare mailing list
        self.client.force_login(self.comunity)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        mde = Mailing.objects.get(email="mde")
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": "|%s|%s|%s|"
                % (self.comunity.id, self.rbatsbak.id, self.krophil.id),
                "subscription_mailing": mde.id,
            },
        )

        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()

        assert "comunity@git.an" in content
        assert "richard@git.an" in content
        assert "krophil@git.an" in content

        # Delete one user
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_REMOVE_SUBSCRIPTION,
                "removal_%d" % mde.id: mde.subscriptions.get(user=self.krophil).id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()

        assert "comunity@git.an" in content
        assert "richard@git.an" in content
        assert "krophil@git.an" not in content

        # Delete multiple users
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_REMOVE_SUBSCRIPTION,
                "removal_%d" % mde.id: [
                    user.id
                    for user in mde.subscriptions.filter(
                        user__in=[self.rbatsbak, self.comunity]
                    ).all()
                ],
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()

        assert "comunity@git.an" not in content
        assert "richard@git.an" not in content
        assert "krophil@git.an" not in content


class ClubSellingViewTest(TestCase):
    """
    Perform basics tests to ensure that the page is available
    """

    @classmethod
    def setUpTestData(cls):
        cls.ae = Club.objects.get(unix_name="ae")
        cls.skia = User.objects.get(username="skia")

    def test_page_not_internal_error(self):
        """
        Test that the page does not return and internal error
        """
        self.client.force_login(self.skia)
        response = self.client.get(
            reverse("club:club_sellings", kwargs={"club_id": self.ae.id})
        )
        assert response.status_code == 200
