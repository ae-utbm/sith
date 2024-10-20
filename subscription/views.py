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

import random

from ajax_select.fields import AutoCompleteSelectField
from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, FormView

from core.models import User
from core.views.forms import SelectDate, SelectDateTime
from subscription.models import Subscription


class SelectionDateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"] = forms.DateTimeField(
            label=_("Start date"), widget=SelectDateTime, required=True
        )
        self.fields["end_date"] = forms.DateTimeField(
            label=_("End date"), widget=SelectDateTime, required=True
        )


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["member", "subscription_type", "payment_method", "location"]

    member = AutoCompleteSelectField("users", required=False, help_text=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields |= forms.fields_for_model(
            User,
            fields=["first_name", "last_name", "email", "date_of_birth"],
            widgets={"date_of_birth": SelectDate},
        )

    def clean_member(self):
        subscriber = self.cleaned_data.get("member")
        if subscriber:
            subscriber = User.objects.filter(id=subscriber.id).first()
        return subscriber

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("member") is None
            and "last_name" not in self.errors.as_data()
            and "first_name" not in self.errors.as_data()
            and "email" not in self.errors.as_data()
            and "date_of_birth" not in self.errors.as_data()
        ):
            self.errors.pop("member", None)
            if self.errors:
                return cleaned_data
            if User.objects.filter(email=cleaned_data.get("email")).first() is not None:
                self.add_error(
                    "email",
                    ValidationError(_("A user with that email address already exists")),
                )
            else:
                u = User(
                    last_name=self.cleaned_data.get("last_name"),
                    first_name=self.cleaned_data.get("first_name"),
                    email=self.cleaned_data.get("email"),
                    date_of_birth=self.cleaned_data.get("date_of_birth"),
                )
                u.generate_username()
                u.set_password(str(random.randrange(1000000, 10000000)))
                u.save()
                cleaned_data["member"] = u
        elif cleaned_data.get("member") is not None:
            self.errors.pop("last_name", None)
            self.errors.pop("first_name", None)
            self.errors.pop("email", None)
            self.errors.pop("date_of_birth", None)
        if cleaned_data.get("member") is None:
            # This should be handled here,
            # but it is done in the Subscription model's clean method
            # TODO investigate why!
            raise ValidationError(
                _(
                    "You must either choose an existing "
                    "user or create a new one properly"
                )
            )
        return cleaned_data


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
