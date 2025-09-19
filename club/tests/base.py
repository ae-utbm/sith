from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker
from model_bakery.recipe import Recipe

from club.models import Club, Membership
from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import User


class TestClub(TestCase):
    """Set up data for test cases related to clubs and membership.

    The generated dataset is the one created by the populate command,
    plus the following modifications :

    - `self.club` is a dummy club
    - `self.club` has two board members :
       simple_board_member (role 3) and president (role 10)
    - `self.club` has one regular member : richard
    - `self.club` has one former member : sli (who had role 2)
    - None of the `self.club` members are in the AE club.
    """

    @classmethod
    def setUpTestData(cls):
        # subscribed users - initial members
        cls.president, cls.simple_board_member = subscriber_user.make(_quantity=2)
        cls.richard = User.objects.get(username="rbatsbak")
        cls.sli = User.objects.get(username="sli")
        cls.root = baker.make(User, is_superuser=True)
        cls.old_subscriber = old_subscriber_user.make()
        cls.public = baker.make(User)

        # subscribed users - not initial member
        cls.krophil = User.objects.get(username="krophil")
        cls.subscriber = subscriber_user.make()

        cls.ae = Club.objects.get(pk=settings.SITH_MAIN_CLUB_ID)
        cls.club = baker.make(Club)
        cls.new_members_url = reverse(
            "club:club_new_members", kwargs={"club_id": cls.club.id}
        )
        cls.members_url = reverse("club:club_members", kwargs={"club_id": cls.club.id})
        a_month_ago = now() - timedelta(days=30)
        yesterday = now() - timedelta(days=1)
        membership_recipe = Recipe(Membership, club=cls.club)
        membership_recipe.make(
            user=cls.simple_board_member, start_date=a_month_ago, role=3
        )
        membership_recipe.make(user=cls.richard, role=1)
        membership_recipe.make(user=cls.president, start_date=a_month_ago, role=10)
        membership_recipe.make(  # sli was a member but isn't anymore
            user=cls.sli, start_date=a_month_ago, end_date=yesterday, role=2
        )

    def setUp(self):
        cache.clear()
