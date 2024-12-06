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
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin, ProcessFormView

from core.views import CanViewMixin
from core.views.forms import LoginForm
from counter.forms import GetUserForm
from counter.models import Counter
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterTabsMixin


class CounterMain(
    CounterTabsMixin, CanViewMixin, DetailView, ProcessFormView, FormMixin
):
    """The public (barman) view."""

    model = Counter
    template_name = "counter/counter_main.jinja"
    pk_url_kwarg = "counter_id"
    form_class = (
        GetUserForm  # Form to enter a client code and get the corresponding user id
    )
    current_tab = "counter"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == "BAR" and not (
            "counter_token" in self.request.session
            and self.request.session["counter_token"] == self.object.token
        ):  # Check the token to avoid the bar to be stolen
            return HttpResponseRedirect(
                reverse_lazy(
                    "counter:details",
                    args=self.args,
                    kwargs={"counter_id": self.object.id},
                )
                + "?bad_location"
            )
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """We handle here the login form for the barman."""
        if self.request.method == "POST":
            self.object = self.get_object()
        self.object.update_activity()
        kwargs = super().get_context_data(**kwargs)
        kwargs["login_form"] = LoginForm()
        kwargs["login_form"].fields["username"].widget.attrs["autofocus"] = True
        kwargs[
            "login_form"
        ].cleaned_data = {}  # add_error fails if there are no cleaned_data
        if "credentials" in self.request.GET:
            kwargs["login_form"].add_error(None, _("Bad credentials"))
        if "sellers" in self.request.GET:
            kwargs["login_form"].add_error(None, _("User is not barman"))
        kwargs["form"] = self.get_form()
        kwargs["form"].cleaned_data = {}  # same as above
        if "bad_location" in self.request.GET:
            kwargs["form"].add_error(
                None, _("Bad location, someone is already logged in somewhere else")
            )
        if self.object.type == "BAR":
            kwargs["barmen"] = self.object.barmen_list
        elif self.request.user.is_authenticated:
            kwargs["barmen"] = [self.request.user]
        if "last_basket" in self.request.session:
            kwargs["last_basket"] = self.request.session.pop("last_basket")
            kwargs["last_customer"] = self.request.session.pop("last_customer")
            kwargs["last_total"] = self.request.session.pop("last_total")
            kwargs["new_customer_amount"] = self.request.session.pop(
                "new_customer_amount"
            )
        return kwargs

    def form_valid(self, form):
        """We handle here the redirection, passing the user id of the asked customer."""
        self.kwargs["user_id"] = form.cleaned_data["user_id"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("counter:click", args=self.args, kwargs=self.kwargs)


class CounterLastOperationsView(CounterTabsMixin, CanViewMixin, DetailView):
    """Provide the last operations to allow barmen to delete them."""

    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = "counter/last_ops.jinja"
    current_tab = "last_ops"

    def dispatch(self, request, *args, **kwargs):
        """We have here again a very particular right handling."""
        self.object = self.get_object()
        if is_logged_in_counter(request) and self.object.barmen_list:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseRedirect(
            reverse("counter:details", kwargs={"counter_id": self.object.id})
            + "?bad_location"
        )

    def get_context_data(self, **kwargs):
        """Add form to the context."""
        kwargs = super().get_context_data(**kwargs)
        threshold = timezone.now() - timedelta(
            minutes=settings.SITH_LAST_OPERATIONS_LIMIT
        )
        kwargs["last_refillings"] = (
            self.object.refillings.filter(date__gte=threshold)
            .select_related("operator", "customer__user")
            .order_by("-id")[:20]
        )
        kwargs["last_sellings"] = (
            self.object.sellings.filter(date__gte=threshold)
            .select_related("seller", "customer__user")
            .order_by("-id")[:20]
        )
        return kwargs


class CounterActivityView(DetailView):
    """Show the bar activity."""

    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = "counter/activity.jinja"
