from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now
from model_bakery import seq
from model_bakery.recipe import Recipe, related

from club.models import Membership
from core.models import User
from subscription.models import Subscription

active_subscription = Recipe(
    Subscription,
    subscription_start=now() - timedelta(days=30),
    subscription_end=now() + timedelta(days=30),
)
ended_subscription = Recipe(
    Subscription,
    subscription_start=now() - timedelta(days=60),
    subscription_end=now() - timedelta(days=30),
)

subscriber_user = Recipe(
    User,
    first_name="subscriber",
    last_name=seq("user "),
    subscriptions=related(active_subscription),
)
"""A user with an active subscription."""

old_subscriber_user = Recipe(
    User,
    first_name="old subscriber",
    last_name=seq("user "),
    subscriptions=related(ended_subscription),
)
"""A user with an ended subscription."""

ae_board_membership = Recipe(
    Membership,
    start_date=now() - timedelta(days=30),
    club_id=settings.SITH_MAIN_CLUB_ID,
    role=settings.SITH_CLUB_ROLES_ID["Board member"],
)

board_user = Recipe(
    User,
    first_name="AE",
    last_name=seq("member "),
    memberships=related(ae_board_membership),
)
"""A user which is in the board of the AE."""
