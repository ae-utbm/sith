from datetime import timedelta

from django.utils.timezone import now
from model_bakery import seq
from model_bakery.recipe import Recipe, related

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
old_subscriber_user = Recipe(
    User,
    first_name="old subscriber",
    last_name=seq("user "),
    subscriptions=related(ended_subscription),
)
