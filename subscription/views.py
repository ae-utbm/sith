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

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.utils.timezone import localdate
from django.views.generic import CreateView, DetailView, TemplateView
from django.views.generic.edit import FormView

from counter.apps import PAYMENT_METHOD
from subscription.forms import (
    SelectionDateForm,
    SubscriptionExistingUserForm,
    SubscriptionNewUserForm,
)
from subscription.models import Subscription


class NewSubscription(PermissionRequiredMixin, TemplateView):
    template_name = "subscription/subscription.jinja"
    permission_required = "subscription.add_subscription"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "existing_user_form": SubscriptionExistingUserForm(
                initial={"member": self.request.GET.get("member")}
            ),
            "new_user_form": SubscriptionNewUserForm(),
            "existing_user_post_url": reverse("subscription:fragment-existing-user"),
            "new_user_post_url": reverse("subscription:fragment-new-user"),
        }


class CreateSubscriptionFragment(PermissionRequiredMixin, CreateView):
    template_name = "subscription/fragments/creation_form.jinja"
    permission_required = "subscription.add_subscription"

    def get_success_url(self):
        return reverse(
            "subscription:creation-success", kwargs={"subscription_id": self.object.id}
        )


class CreateSubscriptionExistingUserFragment(CreateSubscriptionFragment):
    """Create a subscription for a user who already exists."""

    form_class = SubscriptionExistingUserForm
    extra_context = {"post_url": reverse_lazy("subscription:fragment-existing-user")}


class CreateSubscriptionNewUserFragment(CreateSubscriptionFragment):
    """Create a subscription for a user who already exists."""

    form_class = SubscriptionNewUserForm
    extra_context = {"post_url": reverse_lazy("subscription:fragment-new-user")}


class SubscriptionCreatedFragment(PermissionRequiredMixin, DetailView):
    template_name = "subscription/fragments/creation_success.jinja"
    permission_required = "subscription.add_subscription"
    model = Subscription
    pk_url_kwarg = "subscription_id"
    context_object_name = "subscription"


class SubscriptionsStatsView(FormView):
    template_name = "subscription/stats.jinja"
    form_class = SelectionDateForm
    success_url = reverse_lazy("subscriptions:stats")

    def dispatch(self, request, *arg, **kwargs):
        self.start_date = localdate()
        self.end_date = self.start_date
        if request.user.is_root or request.user.is_board_member:
            return super().dispatch(request, *arg, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        self.form = self.get_form()
        self.start_date = self.form["start_date"]
        self.end_date = self.form["end_date"]
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        return {
            "start_date": self.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": self.end_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["subscriptions_total"] = Subscription.objects.filter(
            subscription_end__gte=self.end_date, subscription_start__lte=self.start_date
        )
        kwargs["subscriptions_types"] = settings.SITH_SUBSCRIPTIONS
        kwargs["payment_types"] = PAYMENT_METHOD
        kwargs["locations"] = settings.SITH_SUBSCRIPTION_LOCATIONS
        return kwargs
