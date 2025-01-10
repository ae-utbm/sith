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
import math

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import (
    BaseFormSet,
    Form,
    IntegerField,
    ValidationError,
    formset_factory,
)
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from ninja.main import HttpRequest

from core.auth.mixins import CanViewMixin
from core.models import User
from core.utils import FormFragmentTemplateData
from counter.forms import RefillForm
from counter.models import Counter, Customer, Product, Selling
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterTabsMixin
from counter.views.student_card import StudentCardFormView


def get_operator(request: HttpRequest, counter: Counter, customer: Customer) -> User:
    if counter.type != "BAR":
        return request.user
    if counter.customer_is_barman(customer):
        return customer.user
    return counter.get_random_barman()


class ProductForm(Form):
    quantity = IntegerField(min_value=1)
    id = IntegerField(min_value=0)

    def __init__(
        self,
        customer: Customer,
        counter: Counter,
        allowed_products: dict[int, Product],
        *args,
        **kwargs,
    ):
        self.customer = customer  # Used by formset
        self.counter = counter  # Used by formset
        self.allowed_products = allowed_products
        super().__init__(*args, **kwargs)

    def clean_id(self):
        data = self.cleaned_data["id"]

        # We store self.product so we can use it later on the formset validation
        # And also in the global clean
        self.product = self.allowed_products.get(data, None)
        if self.product is None:
            raise ValidationError(
                _("The selected product isn't available for this user")
            )

        return data

    def clean(self):
        cleaned_data = super().clean()
        if len(self.errors) > 0:
            return

        # Compute prices
        cleaned_data["bonus_quantity"] = 0
        if self.product.tray:
            cleaned_data["bonus_quantity"] = math.floor(
                cleaned_data["quantity"] / Product.QUANTITY_FOR_TRAY_PRICE
            )
        cleaned_data["total_price"] = self.product.price * (
            cleaned_data["quantity"] - cleaned_data["bonus_quantity"]
        )

        return cleaned_data


class BaseBasketForm(BaseFormSet):
    def clean(self):
        super().clean()
        if len(self) == 0:
            return

        self._check_forms_have_errors()
        self._check_recorded_products(self[0].customer)
        self._check_enough_money(self[0].counter, self[0].customer)

    def _check_forms_have_errors(self):
        if any(len(form.errors) > 0 for form in self):
            raise ValidationError(_("Submmited basket is invalid"))

    def _check_enough_money(self, counter: Counter, customer: Customer):
        self.total_price = sum([data["total_price"] for data in self.cleaned_data])
        if self.total_price > customer.amount:
            raise ValidationError(_("Not enough money"))

    def _check_recorded_products(self, customer: Customer):
        """Check for, among other things, ecocups and pitchers"""
        self.total_recordings = 0
        for form in self:
            # form.product is stored by the clean step of each formset form
            if form.product.is_record_product:
                self.total_recordings -= form.cleaned_data["quantity"]
            if form.product.is_unrecord_product:
                self.total_recordings += form.cleaned_data["quantity"]

        if not customer.can_record_more(self.total_recordings):
            raise ValidationError(_("This user have reached his recording limit"))


BasketForm = formset_factory(
    ProductForm, formset=BaseBasketForm, absolute_max=None, min_num=1
)


class CounterClick(CounterTabsMixin, CanViewMixin, SingleObjectMixin, FormView):
    """The click view
    This is a detail view not to have to worry about loading the counter
    Everything is made by hand in the post method.
    """

    model = Counter
    queryset = Counter.objects.annotate_is_open()
    form_class = BasketForm
    template_name = "counter/counter_click.jinja"
    pk_url_kwarg = "counter_id"
    current_tab = "counter"

    def get_queryset(self):
        return super().get_queryset().exclude(type="EBOUTIC").annotate_is_open()

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
            obj.sellers.filter(pk=request.user.pk).exists()
            or not obj.club.has_rights_in_club(request.user)
        ):
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

            for form in formset:
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

            self.customer.recorded_products -= formset.total_recordings
            self.customer.save()

        # Add some info for the main counter view to display
        self.request.session["last_customer"] = self.customer.user.get_display_name()
        self.request.session["last_total"] = f"{formset.total_price:0.2f}"
        self.request.session["new_customer_amount"] = str(self.customer.amount)

        return ret

    def get_success_url(self):
        return resolve_url(self.object)

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
        if self.object.type == "BAR":
            kwargs["student_card_fragment"] = StudentCardFormView.get_template_data(
                self.customer
            ).render(self.request)

        if self.object.can_refill():
            kwargs["refilling_fragment"] = RefillingCreateView.get_template_data(
                self.customer
            ).render(self.request)

        return kwargs


class RefillingCreateView(FormView):
    """This is a fragment only view which integrates with counter_click.jinja"""

    form_class = RefillForm
    template_name = "counter/fragments/create_refill.jinja"

    @classmethod
    def get_template_data(
        cls, customer: Customer, *, form_instance: form_class | None = None
    ) -> FormFragmentTemplateData[form_class]:
        return FormFragmentTemplateData(
            form=form_instance if form_instance else cls.form_class(),
            template=cls.template_name,
            context={
                "action": reverse_lazy(
                    "counter:refilling_create", kwargs={"customer_id": customer.pk}
                ),
            },
        )

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

    def form_valid(self, form):
        res = super().form_valid(form)
        form.clean()
        form.instance.counter = self.counter
        form.instance.operator = self.operator
        form.instance.customer = self.customer
        form.instance.save()
        return res

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.get_template_data(self.customer, form_instance=context["form"])
        context.update(data.context)
        return context

    def get_success_url(self, **kwargs):
        return self.request.path
