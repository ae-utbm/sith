#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from django.urls import path

from subscription.views import (
    CreateSubscriptionExistingUserFragment,
    CreateSubscriptionNewUserFragment,
    NewSubscription,
    SubscriptionCreatedFragment,
    SubscriptionPermissionView,
    SubscriptionsStatsView,
)

urlpatterns = [
    # Subscription views
    path("", NewSubscription.as_view(), name="subscription"),
    path(
        "fragment/existing-user/",
        CreateSubscriptionExistingUserFragment.as_view(),
        name="fragment-existing-user",
    ),
    path(
        "fragment/new-user/",
        CreateSubscriptionNewUserFragment.as_view(),
        name="fragment-new-user",
    ),
    path(
        "fragment/<int:subscription_id>/creation-success",
        SubscriptionCreatedFragment.as_view(),
        name="creation-success",
    ),
    path(
        "perms/",
        SubscriptionPermissionView.as_view(),
        name="perms",
    ),
    path("stats/", SubscriptionsStatsView.as_view(), name="stats"),
]
