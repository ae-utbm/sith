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

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse
from django.utils.safestring import SafeString
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from ninja.main import HttpRequest

from core.auth.mixins import CanViewMixin
from core.models import User
from core.views.mixins import FragmentMixin, UseFragmentsMixin
from counter.forms import BasketForm, RefillForm
from counter.models import (
    Counter,
    Customer,
    ReturnableProduct,
    Selling,
)
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterTabsMixin
from counter.views.student_card import StudentCardFormFragment


def get_operator(request: HttpRequest, counter: Counter, customer: Customer) -> User:
    if counter.type != "BAR":
        return request.user
    if counter.customer_is_barman(customer):
        return customer.user
    return counter.get_random_barman()


class CounterClick(
    CounterTabsMixin, UseFragmentsMixin, CanViewMixin, SingleObjectMixin, FormView
):
    """The click view
    This is a detail view not to have to worry about loading the counter
    Everything is made by hand in the post method.
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
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {
            "customer": self.customer,
            "counter": self.object,
            "allowed_products": {product.id: product for product in self.products},
        }
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, user__id=self.kwargs["user_id"])
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

        if obj.type == "BAR" and (
            not obj.is_open
            or "counter_token" not in request.session
            or request.session["counter_token"] != obj.token
        ):
            return redirect(obj)  # Redirect to counter

        self.products = obj.get_products_for(self.customer)

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
            for form in sorted(formset, key=lambda form: form.product.price):
                self.request.session["last_basket"].append(
                    f"{form.cleaned_data['quantity']} x {form.product.name}"
                )

                Selling(
                    label=form.product.name,
                    product=form.product,
                    club=form.product.club,
                    counter=self.object,
                    unit_price=form.product.price,
                    quantity=form.cleaned_data["quantity"]
                    - form.cleaned_data["bonus_quantity"],
                    seller=operator,
                    customer=self.customer,
                ).save()
                if form.cleaned_data["bonus_quantity"] > 0:
                    Selling(
                        label=f"{form.product.name} (Plateau)",
                        product=form.product,
                        club=form.product.club,
                        counter=self.object,
                        unit_price=0,
                        quantity=form.cleaned_data["bonus_quantity"],
                        seller=operator,
                        customer=self.customer,
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
        if self.object.can_refill():
            res["refilling_fragment"] = RefillingCreateView.as_fragment()(
                self.request, customer=self.customer
            )
        return res

    def get_context_data(self, **kwargs):
        """Add customer to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["products"] = self.products
        kwargs["categories"] = {}
        for product in kwargs["products"]:
            if product.product_type:
                kwargs["categories"].setdefault(product.product_type, []).append(
                    product
                )
        kwargs["customer"] = self.customer
        kwargs["cancel_url"] = self.get_success_url()

        # To get all forms errors to the javascript, we create a list of error list
        kwargs["form_errors"] = [
            list(field_error.values()) for field_error in kwargs["form"].errors
        ]
        return kwargs


class RefillingCreateView(FragmentMixin, FormView):
    """This is a fragment only view which integrates with counter_click.jinja"""

    form_class = RefillForm
    template_name = "counter/fragments/create_refill.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.customer: Customer = get_object_or_404(Customer, pk=kwargs["customer_id"])
        if not self.customer.can_buy:
            raise Http404

        if not is_logged_in_counter(request):
            raise PermissionDenied

        self.counter: Counter = get_object_or_404(
            Counter, token=request.session["counter_token"]
        )

        if not self.counter.can_refill():
            raise PermissionDenied

        self.operator = get_operator(request, self.counter, self.customer)

        return super().dispatch(request, *args, **kwargs)

    def render_fragment(self, request, **kwargs) -> SafeString:
        self.customer = kwargs.pop("customer")
        return super().render_fragment(request, **kwargs)

    def form_valid(self, form):
        res = super().form_valid(form)
        form.clean()
        form.instance.counter = self.counter
        form.instance.operator = self.operator
        form.instance.customer = self.customer
        form.instance.save()
        return res

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["action"] = reverse(
            "counter:refilling_create", kwargs={"customer_id": self.customer.pk}
        )
        return kwargs

    def get_success_url(self, **kwargs):
        return self.request.path
