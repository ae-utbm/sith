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
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.urls import reverse
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, TemplateView

from core.views import FragmentMixin, UseFragmentsMixin
from core.views.group import PermissionGroupsUpdateView
from subscription.forms import (
    SubscriptionExistingUserForm,
    SubscriptionNewUserForm,
)
from subscription.models import Subscription


class CreateSubscriptionFragment(PermissionRequiredMixin, FragmentMixin, CreateView):
    permission_required = "subscription.add_subscription"
    object = None

    def get_success_url(self):
        return reverse(
            "subscription:creation-success", kwargs={"subscription_id": self.object.id}
        )


class CreateSubscriptionExistingUserFragment(CreateSubscriptionFragment):
    """Create a subscription for a user who already exists."""

    form_class = SubscriptionExistingUserForm
    template_name = "subscription/fragments/creation_form_existing_user.jinja"


class CreateSubscriptionNewUserFragment(CreateSubscriptionFragment):
    """Create a subscription for a user who doesn't exist yet."""

    form_class = SubscriptionNewUserForm
    template_name = "subscription/fragments/creation_form_new_user.jinja"

    def form_valid(self, form):
        res = super().form_valid(form)
        reset_form = PasswordResetForm({"email": form.cleaned_data["email"]})
        if reset_form.is_valid():
            reset_form.save(
                use_https=True,
                email_template_name="core/new_user_email.jinja",
                subject_template_name="core/new_user_email_subject.jinja",
                from_email="ae@utbm.fr",
            )
        return res


class NewSubscription(PermissionRequiredMixin, UseFragmentsMixin, TemplateView):
    template_name = "subscription/subscription.jinja"
    permission_required = "subscription.add_subscription"
    fragments = {
        "new_user_fragment": CreateSubscriptionNewUserFragment,
        "existing_user_fragment": CreateSubscriptionExistingUserFragment,
    }


class SubscriptionCreatedFragment(PermissionRequiredMixin, DetailView):
    template_name = "subscription/fragments/creation_success.jinja"
    permission_required = "subscription.add_subscription"
    model = Subscription
    pk_url_kwarg = "subscription_id"
    context_object_name = "subscription"


class SubscriptionPermissionView(PermissionGroupsUpdateView):
    """Manage the groups that have access to the subscription creation page."""

    permission = "subscription.add_subscription"
    extra_context = {"object_name": _("the groups that can create subscriptions")}


class SubscriptionsStatsView(TemplateView):
    template_name = "subscription/stats.jinja"

    def dispatch(self, request, *arg, **kwargs):
        if request.user.is_root or request.user.is_board_member:
            return super().dispatch(request, *arg, **kwargs)
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        today = localdate()
        qs = Subscription.objects.filter(
            subscription_end__gte=today, subscription_start__lte=today
        )
        grouped = qs.values("subscription_type", "location", "payment_method").annotate(
            count=Count("*")
        )
        by_location = qs.values("location").annotate(count=Count("*"))
        by_type = qs.values("subscription_type").annotate(count=Count("*"))
        kwargs["subscriptions"] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        for sub in grouped:
            kwargs["subscriptions"][sub["subscription_type"]][sub["location"]][
                sub["payment_method"]
            ] = sub["count"]
        kwargs["total_location"] = defaultdict(
            int, {i["location"]: i["count"] for i in by_location}
        )
        kwargs["total_type"] = defaultdict(
            int, {i["subscription_type"]: i["count"] for i in by_type}
        )

        kwargs["subscriptions_types"] = settings.SITH_SUBSCRIPTIONS
        kwargs["payment_types"] = settings.SITH_SUBSCRIPTION_PAYMENT_METHOD
        kwargs["locations"] = settings.SITH_SUBSCRIPTION_LOCATIONS
        return kwargs
