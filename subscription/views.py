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

import secrets

from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView

from subscription.forms import SelectionDateForm, SubscriptionForm
from subscription.models import Subscription


class NewSubscription(CreateView):
    template_name = "subscription/subscription.jinja"
    form_class = SubscriptionForm

    def dispatch(self, request, *arg, **kwargs):
        if request.user.can_create_subscription:
            return super().dispatch(request, *arg, **kwargs)
        raise PermissionDenied

    def get_initial(self):
        if "member" in self.request.GET:
            return {
                "member": self.request.GET["member"],
                "subscription_type": "deux-semestres",
            }
        return {"subscription_type": "deux-semestres"}

    def form_valid(self, form):
        form.instance.subscription_start = Subscription.compute_start(
            duration=settings.SITH_SUBSCRIPTIONS[form.instance.subscription_type][
                "duration"
            ],
            user=form.instance.member,
        )
        form.instance.subscription_end = Subscription.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS[form.instance.subscription_type][
                "duration"
            ],
            start=form.instance.subscription_start,
            user=form.instance.member,
        )
        return super().form_valid(form)


class SubscriptionsStatsView(FormView):
    template_name = "subscription/stats.jinja"
    form_class = SelectionDateForm

    def dispatch(self, request, *arg, **kwargs):
        import datetime

        self.start_date = datetime.datetime.today()
        self.end_date = self.start_date
        res = super().dispatch(request, *arg, **kwargs)
        if request.user.is_root or request.user.is_board_member:
            return res
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        self.form = self.get_form()
        self.start_date = self.form["start_date"]
        self.end_date = self.form["end_date"]
        res = super().post(request, *args, **kwargs)
        if request.user.is_root or request.user.is_board_member:
            return res
        raise PermissionDenied

    def get_initial(self):
        init = {
            "start_date": self.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": self.end_date.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return init

    def get_context_data(self, **kwargs):
        from subscription.models import Subscription

        kwargs = super().get_context_data(**kwargs)
        kwargs["subscriptions_total"] = Subscription.objects.filter(
            subscription_end__gte=self.end_date, subscription_start__lte=self.start_date
        )
        kwargs["subscriptions_types"] = settings.SITH_SUBSCRIPTIONS
        kwargs["payment_types"] = settings.SITH_COUNTER_PAYMENT_METHOD
        kwargs["locations"] = settings.SITH_SUBSCRIPTION_LOCATIONS
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy("subscriptions:stats")
