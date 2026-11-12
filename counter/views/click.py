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
from collections import defaultdict
from typing import TYPE_CHECKING

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView, FormView
from django.views.generic.detail import SingleObjectMixin

from core.auth.mixins import CanViewMixin
from core.views.mixins import FragmentMixin, UseFragmentsMixin
from counter.forms import BasketForm, RefillForm
from counter.models import (
    Counter,
    Customer,
    ProductFormula,
    Refilling,
    ReturnableProduct,
    Selling,
)
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterTabsMixin
from counter.views.student_card import StudentCardFormFragment

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.utils.safestring import SafeString

    from core.models import User


def get_operator(request: HttpRequest, counter: Counter, customer: Customer) -> User:
    if counter.type != "BAR":
        return request.user
    if counter.customer_is_barman(customer):
        return customer.user
    return random.choice(list(request.barmen))


class CounterClick(
    CounterTabsMixin, UseFragmentsMixin, CanViewMixin, SingleObjectMixin, FormView
):
    """The click view.

    This page is reached from the counter main page, after selecting
    the user who is purchasing stuff.

    # Counter access

    Who can perform barman actions depends on the type of the counter :

    - for eboutic counters, no barman access at all is granted ;
      it's just a 404, as there should be only one eboutic,
      accessible only at `/eboutic/`
    - office counters are accessible to the board members of the
      club owning the counter and to users that have been
      explicitly added to the sellers of this counter.
    - bar counters are accessible to users that have been added to
      the counter sellers and that are currently logged as barmen
      on the current device.

    The bar case is really tricky,
    as it doesn't use the usual django auth backend.
    Barmen must not be logged in as regular users,
    but as barmen, granting the session some special privileges,
    even in the case where no regular user is logged in.

    This is because of two reasons :

    - we track the barmen connection, for logging,
      statistics and dick contest purposes.
      We want to know who was barman, where and when,
      as barmen are accountable of what happens during their duty.
    - multiple users must be able to log on the same device,
      while keeping the session anonymous.
      The bar PC must be a reliable way for any barman to click users,
      but without requiring a user session.
      Just imagine if someone who is superuser had to log in with
      all its privileges on a device everyone can access.

    # Available items

    A counter can have multiple products.
    A product can have multiple prices.
    To select what the user can buy, we select
    all the prices that can be applied to the current
    customer, among the products of the counter.
    The price selection logic is described in
    [PriceQuerySet][counter.models.PriceQuerySet].

    On top of that, some additional rules are applied,
    because alcohol can be sold on counters :

    - if the customer is minor (or has not filled its birthdate)
      age restricted products are removed
      ([L.3342-1, Code de la santé publique](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000031927682))
    - if any barman on the current device is minor,
      age restricted products are also removed
      ([L.3336-4, Code de la santé publique](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048654800))

    The minor barman case is a little bit unclear, legally speaking,
    as barmen are volunteers, but the law speaks only of employees and interns.
    As such, we don't apply the law to its full extent.
    It would be harsh for young students not to be able to
    be barmen at the MDE, where no alcohol at all is sold during daytime.
    However, we restrict items that can be sold as a token of good will.
    """

    model = Counter
    queryset = (
        Counter.objects.exclude(type="EBOUTIC")
        .annotate_is_open()
        .select_related("club")
    )
    form_class = BasketForm
    template_name = "counter/counter_click.jinja"
    pk_url_kwarg = "counter_id"
    current_tab = "counter"

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "customer": self.customer,
            "counter": self.object,
            "form_kwargs": {
                "allowed_prices": {price.id: price for price in self.prices}
            },
        }

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, user_id=self.kwargs["user_id"])
        obj: Counter = self.get_object()

        if not self.customer.can_buy or self.customer.user.is_banned_counter:
            return redirect(obj)  # Redirect to counter

        if obj.type == "OFFICE" and (
            request.user.is_anonymous
            or not (
                obj.sellers.contains(request.user)
                or obj.club.has_rights_in_club(request.user)
            )
        ):
            # To be able to click on an office counter,
            # a user must either be in the board of the club that own the counter
            # or a seller of this counter.
            raise PermissionDenied

        if obj.type == "BAR" and not (
            request.barmen and request.barmen.issubset(set(obj.barmen_list))
        ):
            messages.error(request, _("You cannot click users on this counter"))
            return redirect(obj)  # Redirect to counter

        self.prices = list(obj.get_prices_for(self.customer))
        if any(user.age < 18 for user in request.barmen):
            # users without a birthdate cannot be sellers on counters,
            # so the `user.age == 0` case shouldn't happen
            filtered = [p for p in self.prices if p.product.limit_age < 18]
            if len(filtered) != len(self.prices):
                self.prices = filtered
                messages.warning(
                    request,
                    _(
                        "A minor is barman on this on this device, "
                        "so you cannot currently sell alcohol."
                    ),
                )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, formset):
        ret = super().form_valid(formset)

        if len(formset) == 0:
            return ret

        operator = get_operator(self.request, self.object, self.customer)
        with transaction.atomic():
            self.request.session["last_basket"] = []

            # We sort items from cheap to expensive
            # This is important because some items have a negative price
            # Negative priced items gives money to the customer and should
            # be processed first so that we don't throw a not enough money error
            for form in sorted(formset, key=lambda form: form.price.amount):
                self.request.session["last_basket"].append(
                    f"{form.cleaned_data['quantity']} x {form.price.full_label}"
                )

                common_kwargs = {
                    "product": form.price.product,
                    "club_id": form.price.product.club_id,
                    "counter": self.object,
                    "seller": operator,
                    "customer": self.customer,
                }
                Selling(
                    **common_kwargs,
                    label=form.price.full_label,
                    unit_price=form.price.amount,
                    quantity=form.cleaned_data["quantity"]
                    - form.cleaned_data["bonus_quantity"],
                ).save()
                if form.cleaned_data["bonus_quantity"] > 0:
                    Selling(
                        **common_kwargs,
                        label=f"{form.price.full_label} (Plateau)",
                        unit_price=0,
                        quantity=form.cleaned_data["bonus_quantity"],
                    ).save()

            self.customer.update_returnable_balance()

        # Add some info for the main counter view to display
        self.request.session["last_customer"] = self.customer.user.get_display_name()
        self.request.session["last_total"] = f"{formset.total_price:0.2f}"
        self.request.session["new_customer_amount"] = str(self.customer.amount)

        return ret

    def _update_returnable_balance(self, formset):
        ids = [form.cleaned_data["id"] for form in formset]
        returnables = list(
            ReturnableProduct.objects.filter(
                Q(product_id__in=ids) | Q(returned_product_id__in=ids)
            ).annotate_balance_for(self.customer)
        )
        for returnable in returnables:
            cons_quantity = next(
                (
                    form.cleaned_data["quantity"]
                    for form in formset
                    if form.cleaned_data["id"] == returnable.product_id
                ),
                0,
            )
            dcons_quantity = next(
                (
                    form.cleaned_data["quantity"]
                    for form in formset
                    if form.cleaned_data["id"] == returnable.returned_product_id
                ),
                0,
            )
            self.customer.return_balances.update_or_create(
                returnable=returnable,
                defaults={
                    "balance": returnable.balance + cons_quantity - dcons_quantity
                },
            )

    def get_success_url(self):
        return resolve_url(self.object)

    def get_fragment_context_data(self) -> dict[str, SafeString]:
        res = super().get_fragment_context_data()
        if self.object.type == "BAR":
            res["student_card_fragment"] = StudentCardFormFragment.as_fragment()(
                self.request, customer=self.customer
            )
        if self.object.can_refill:
            res["refilling_fragment"] = RefillingCreateView.as_fragment()(
                self.request, customer=self.customer, counter=self.object
            )
        return res

    def get_context_data(self, **kwargs):
        """Add customer to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["prices"] = self.prices
        kwargs["formulas"] = ProductFormula.objects.filter(
            result__in=[p.product_id for p in self.prices]
        ).prefetch_related("products")
        kwargs["categories"] = defaultdict(list)
        for price in self.prices:
            kwargs["categories"][price.product.product_type].append(price)
        kwargs["customer"] = self.customer
        kwargs["cancel_url"] = self.get_success_url()

        # To get all forms errors to the javascript, we create a list of error list
        kwargs["form_errors"] = [
            list(field_error.values()) for field_error in kwargs["form"].errors
        ]
        return kwargs


class RefillingCreateView(FragmentMixin, CreateView):
    """This is a fragment only view which integrates with counter_click.jinja"""

    model = Refilling
    form_class = RefillForm
    template_name = "counter/fragments/create_refill.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.customer: Customer = get_object_or_404(Customer, pk=kwargs["customer_id"])
        if not self.customer.can_buy:
            raise Http404

        self.counter: Counter = get_object_or_404(Counter, id=self.kwargs["counter_id"])

        if (
            not is_logged_in_counter(request, counter=self.counter)
            or not self.counter.can_refill
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def render_fragment(self, request, **kwargs) -> SafeString:
        self.customer = kwargs.pop("customer")
        self.counter = kwargs.pop("counter")
        self.object = None
        return super().render_fragment(request, **kwargs)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "counter": self.counter,
            "operator": get_operator(self.request, self.counter, self.customer),
            "customer": self.customer,
        }

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["action"] = reverse(
            "counter:refilling_create",
            kwargs={"customer_id": self.customer.pk, "counter_id": self.counter.pk},
        )
        return kwargs

    def get_success_url(self, **kwargs):
        return self.request.path
