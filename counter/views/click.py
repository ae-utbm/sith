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
from django.db.models import F
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

from core.models import User
from core.utils import FormFragmentTemplateData
from core.views import CanViewMixin
from counter.forms import RefillForm
from counter.models import Counter, Customer, Product, Selling
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterTabsMixin
from counter.views.student_card import StudentCardFormView


def get_operator(counter: Counter, customer: Customer) -> User:
    if counter.customer_is_barman(customer):
        return customer.user
    return counter.get_random_barman()


class ProductForm(Form):
    quantity = IntegerField(min_value=1)
    id = IntegerField(min_value=0)

    def __init__(
        self,
        *args,
        customer: Customer | None = None,
        counter: Counter | None = None,
        **kwargs,
    ):
        self.customer = customer
        self.counter = counter
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.customer is None or self.counter is None:
            raise RuntimeError(
                f"{self} has been initialized without customer or counter"
            )

        user = self.customer.user

        # We store self.product so we can use it later on the formset validation
        self.product = self.counter.products.filter(id=cleaned_data["id"]).first()
        if self.product is None:
            raise ValidationError(
                _(
                    "Product %(product)s doesn't exist or isn't available on this counter"
                )
                % {"product": cleaned_data["id"]}
            )

        # Test alcohoolic products
        if self.product.limit_age >= 18:
            if not user.date_of_birth:
                raise ValidationError(_("Too young for that product"))
            if user.is_banned_alcohol:
                raise ValidationError(_("Not allowed for that product"))
        if user.date_of_birth and self.customer.user.get_age() < self.product.limit_age:
            raise ValidationError(_("Too young for that product"))

        if user.is_banned_counter:
            raise ValidationError(_("Not allowed for that product"))

        # Compute prices
        cleaned_data["bonus_quantity"] = 0
        if self.product.tray:
            cleaned_data["bonus_quantity"] = math.floor(
                cleaned_data["quantity"] / Product.QUANTITY_FOR_TRAY_PRICE
            )
        cleaned_data["unit_price"] = self.product.get_actual_price(
            self.counter, self.customer
        )
        cleaned_data["total_price"] = cleaned_data["unit_price"] * (
            cleaned_data["quantity"] - cleaned_data["bonus_quantity"]
        )

        return cleaned_data


class BaseBasketForm(BaseFormSet):
    def clean(self):
        super().clean()
        if len(self) == 0:
            return
        self._check_recorded_products(self[0].customer)
        self._check_enough_money(self[0].counter, self[0].customer)

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {
            "customer": self.customer,
            "counter": self.object,
        }
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, user__id=self.kwargs["user_id"])
        obj: Counter = self.get_object()
        if not self.customer.can_buy:
            raise Http404
        if obj.type != "BAR" and not request.user.is_authenticated:
            raise PermissionDenied
        if obj.type == "BAR" and (
            "counter_token" not in request.session
            or request.session["counter_token"] != obj.token
            or len(obj.barmen_list) == 0
        ):
            return redirect(obj)  # Redirect to counter
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, formset):
        ret = super().form_valid(formset)

        if len(formset) == 0:
            return ret

        operator = get_operator(self.object, self.customer)
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
                    unit_price=form.cleaned_data["unit_price"],
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

    def get_product(self, pid):
        return Product.objects.filter(pk=int(pid)).first()

    def get_context_data(self, **kwargs):
        """Add customer to the context."""
        kwargs = super().get_context_data(**kwargs)
        products = self.object.products.select_related("product_type")

        # Optimisation to bulk edit prices instead of `calling get_actual_price` on everything
        if self.object.customer_is_barman(self.customer):
            products = products.annotate(price=F("special_selling_price"))
        else:
            products = products.annotate(price=F("selling_price"))

        kwargs["products"] = products
        kwargs["categories"] = {}
        for product in kwargs["products"]:
            if product.product_type:
                kwargs["categories"].setdefault(product.product_type, []).append(
                    product
                )
        kwargs["customer"] = self.customer

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

        self.operator = get_operator(self.counter, self.customer)

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
