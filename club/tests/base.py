from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker

from club.models import Club, Membership
from core.models import User


class TestClub(TestCase):
    """Set up data for test cases related to clubs and membership.

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

        cls.ae = Club.objects.get(pk=settings.SITH_MAIN_CLUB_ID)
        cls.club = baker.make(Club)
        cls.members_url = reverse("club:club_members", kwargs={"club_id": cls.club.id})
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
