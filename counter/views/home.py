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
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView

from core.auth.mixins import CanViewMixin
from core.views import FragmentMixin, UseFragmentsMixin
from counter.forms import CounterLoginForm, GetUserForm
from counter.models import Counter, Permanency
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterTabsMixin


class CounterLoginFragment(FragmentMixin, SingleObjectMixin, FormView):
    model = Counter
    form_class = CounterLoginForm
    reload_on_redirect = True
    pk_url_kwarg = "counter_id"
    template_name = "counter/fragments/login.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"counter": self.object}

    def form_valid(self, form: CounterLoginForm):
        self.object.permanencies.create(user=form.get_user(), start=timezone.now())
        if not self.object.barmen_list:
            self.object.gen_token()
        self.request.session["counter_token"] = self.object.token
        self.success_url = reverse(
            "counter:details", kwargs={"counter_id": self.object.id}
        )
        return super().form_valid(form)

    def render_fragment(self, request, **kwargs) -> SafeString:
        self.object = kwargs.pop("counter")
        return super().render_fragment(request, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "action": reverse("counter:login", kwargs={"counter_id": self.object.id})
        }


@require_POST
def counter_logout(request: HttpRequest, counter_id: int) -> HttpResponseRedirect:
    """End the permanency of a user in this counter."""
    Permanency.objects.filter(
        counter=counter_id, user=request.POST["user_id"], end=None
    ).update(end=F("activity"))
    return redirect("counter:details", counter_id=counter_id)


class CounterMain(
    CounterTabsMixin, UseFragmentsMixin, CanViewMixin, SingleObjectMixin, FormView
):
    """The public (barman) view."""

    model = Counter
    queryset = Counter.objects.annotate_is_open().exclude(type="EBOUTIC")
    template_name = "counter/counter_main.jinja"
    pk_url_kwarg = "counter_id"
    form_class = GetUserForm
    current_tab = "counter"

    def dispatch(self, request, *args, **kwargs):
        self.object: Counter = self.get_object()
        if self.object.type != "BAR" and self.request.method.upper() == "POST":
            # barmen have to log in (thus do a POST request)
            # only if it is a bar.
            return self.http_method_not_allowed(request, *args, **kwargs)
        if self.object.type == "BAR":
            self.object.update_activity()
        return super().dispatch(request, *args, **kwargs)

    def get_fragment_context_data(self) -> dict[str, SafeString]:
        login_fragment = (
            CounterLoginFragment.as_fragment()(self.request, counter=self.object)
            if self.object.type == "BAR"
            else ""
        )
        return super().get_fragment_context_data() | {"login_fragment": login_fragment}

    def get_context_data(self, **kwargs):
        """We handle here the login form for the barman."""
        kwargs = super().get_context_data(**kwargs)
        if self.object.type == "BAR":
            kwargs["barmen"] = self.object.barmen_list
        kwargs["can_click"] = (
            self.object.type == "BAR"
            and self.object.is_open
            and self.request.session.get("counter_token", "") == self.object.token
        ) or (
            self.object.type == "OFFICE"
            and (
                self.object.sellers.contains(self.request.user)
                or self.object.club.has_rights_in_club(self.request.user)
            )
        )
        if "last_basket" in self.request.session:
            kwargs["last_basket"] = self.request.session.pop("last_basket")
            kwargs["last_customer"] = self.request.session.pop("last_customer")
            kwargs["last_total"] = self.request.session.pop("last_total")
            kwargs["new_customer_amount"] = self.request.session.pop(
                "new_customer_amount"
            )
        return kwargs

    def form_valid(self, form: CounterLoginForm):
        """We handle here the redirection, passing the user id of the asked customer."""
        self.success_url = reverse(
            "counter:click",
            kwargs={
                "counter_id": self.kwargs["counter_id"],
                "user_id": form.cleaned_data["user_id"],
            },
        )
        return super().form_valid(form)


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
