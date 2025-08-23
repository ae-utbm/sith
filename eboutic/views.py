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

from __future__ import annotations

import base64
import contextlib
import json
from typing import TYPE_CHECKING

import sentry_sdk
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.db import DatabaseError, transaction
from django.db.models import Subquery
from django.db.models.fields import forms
from django.db.utils import cached_property
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, FormView, UpdateView, View
from django.views.generic.edit import SingleObjectMixin
from django_countries.fields import Country

from core.auth.mixins import CanViewMixin
from core.views.mixins import FragmentMixin, UseFragmentsMixin
from counter.forms import BaseBasketForm, BillingInfoForm, ProductForm
from counter.models import (
    BillingInfo,
    Customer,
    Product,
    Refilling,
    Selling,
    get_eboutic,
)
from eboutic.models import (
    Basket,
    BasketItem,
    BillingInfoState,
    Invoice,
    InvoiceItem,
    get_eboutic_products,
)

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
    from django.utils.html import SafeString


class BaseEbouticBasketForm(BaseBasketForm):
    def _check_enough_money(self, *args, **kwargs):
        # Disable money check
        ...


EbouticBasketForm = forms.formset_factory(
    ProductForm, formset=BaseEbouticBasketForm, absolute_max=None, min_num=1
)


class EbouticMainView(LoginRequiredMixin, FormView):
    """Main view of the eboutic application.

    The purchasable products are those of the eboutic which
    belong to a category of products of a product category
    (orphan products are inaccessible).

    """

    template_name = "eboutic/eboutic_main.jinja"
    form_class = EbouticBasketForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {
            "customer": self.customer,
            "counter": get_eboutic(),
            "allowed_products": {product.id: product for product in self.products},
        }
        return kwargs

    def form_valid(self, formset):
        if len(formset) == 0:
            formset.errors.append(_("Your basket is empty"))
            return self.form_invalid(formset)

        with transaction.atomic():
            self.basket = Basket.objects.create(user=self.request.user)
            for form in formset:
                BasketItem.from_product(
                    form.product, form.cleaned_data["quantity"], self.basket
                ).save()
            self.basket.save()
        return super().form_valid(formset)

    def get_success_url(self):
        return reverse("eboutic:checkout", kwargs={"basket_id": self.basket.id})

    @cached_property
    def products(self) -> list[Product]:
        return get_eboutic_products(self.request.user)

    @cached_property
    def customer(self) -> Customer:
        return Customer.get_or_create(self.request.user)[0]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.products
        context["customer_amount"] = self.request.user.account_balance

        purchases = (
            Customer.objects.filter(pk=self.customer.pk)
            .annotate(
                last_refill=Subquery(
                    Refilling.objects.filter(
                        counter__type="EBOUTIC", customer_id=self.customer.pk
                    )
                    .order_by("-date")
                    .values("date")[:1]
                ),
                last_purchase=Subquery(
                    Selling.objects.filter(
                        counter__type="EBOUTIC", customer_id=self.customer.pk
                    )
                    .order_by("-date")
                    .values("date")[:1]
                ),
            )
            .values_list("last_refill", "last_purchase")
        )[0]

        purchase_times = [
            int(purchase.timestamp() * 1000)
            for purchase in purchases
            if purchase is not None
        ]

        context["last_purchase_time"] = (
            max(purchase_times) if len(purchase_times) > 0 else "null"
        )
        return context


@require_GET
@login_required
def payment_result(request, result: str) -> HttpResponse:
    context = {"success": result == "success"}
    return render(request, "eboutic/eboutic_payment_result.jinja", context)


class BillingInfoFormFragment(
    LoginRequiredMixin, FragmentMixin, SuccessMessageMixin, UpdateView
):
    """Update billing info"""

    model = BillingInfo
    form_class = BillingInfoForm
    template_name = "eboutic/eboutic_billing_info.jinja"
    success_message = _("Billing info registration success")

    def get_initial(self):
        if self.object is None:
            return {
                "country": Country(code="FR"),
            }
        return {}

    def render_fragment(self, request, **kwargs) -> SafeString:
        self.object = self.get_object()
        return super().render_fragment(request, **kwargs)

    @cached_property
    def customer(self) -> Customer:
        return Customer.get_or_create(self.request.user)[0]

    def form_valid(self, form: BillingInfoForm):
        form.instance.customer = self.customer
        return super().form_valid(form)

    def get_object(self, *args, **kwargs):
        # if a BillingInfo already exists, this view will behave like an UpdateView
        # otherwise, it will behave like a CreateView.
        return getattr(self.customer, "billing_infos", None)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["billing_infos_state"] = BillingInfoState.from_model(self.object)
        kwargs["action"] = reverse("eboutic:billing_infos")
        match BillingInfoState.from_model(self.object):
            case BillingInfoState.EMPTY:
                messages.warning(
                    self.request,
                    _(
                        "You must fill your billing infos if you want to pay with your credit card"
                    ),
                )
            case BillingInfoState.MISSING_PHONE_NUMBER:
                messages.warning(
                    self.request,
                    _(
                        "The Crédit Agricole changed its policy related to the billing "
                        + "information that must be provided in order to pay with a credit card. "
                        + "If you want to pay with your credit card, you must add a phone number "
                        + "to the data you already provided.",
                    ),
                )
        return kwargs

    def get_success_url(self, **kwargs):
        return self.request.path


class EbouticCheckout(CanViewMixin, UseFragmentsMixin, DetailView):
    model = Basket
    pk_url_kwarg = "basket_id"
    context_object_name = "basket"
    template_name = "eboutic/eboutic_checkout.jinja"
    fragments = {
        "billing_infos_form": BillingInfoFormFragment,
    }

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if hasattr(self.request.user, "customer"):
            customer = self.request.user.customer
            kwargs["customer_amount"] = customer.amount
        else:
            kwargs["customer_amount"] = None
        kwargs["billing_infos"] = {}

        with contextlib.suppress(BillingInfo.DoesNotExist):
            kwargs["billing_infos"] = json.dumps(
                dict(self.object.get_e_transaction_data())
            )
        return kwargs


class EbouticPayWithSith(CanViewMixin, SingleObjectMixin, View):
    model = Basket
    pk_url_kwarg = "basket_id"

    def post(self, request, *args, **kwargs):
        basket = self.get_object()
        refilling = settings.SITH_COUNTER_PRODUCTTYPE_REFILLING
        if basket.items.filter(type_id=refilling).exists():
            messages.error(
                self.request,
                _("You can't buy a refilling with sith money"),
            )
            return redirect("eboutic:payment_result", "failure")

        eboutic = get_eboutic()
        sales = basket.generate_sales(eboutic, basket.user, "SITH_ACCOUNT")
        try:
            with transaction.atomic():
                # Selling.save has some important business logic in it.
                # Do not bulk_create this
                for sale in sales:
                    sale.save()
                basket.delete()
            return redirect("eboutic:payment_result", "success")
        except DatabaseError as e:
            sentry_sdk.capture_exception(e)
        except ValidationError as e:
            messages.error(self.request, e.message)
        return redirect("eboutic:payment_result", "failure")


class EtransactionAutoAnswer(View):
    # Response documentation
    # https://www1.paybox.com/espace-integrateur-documentation/la-solution-paybox-system/gestion-de-la-reponse/
    def get(self, request, *args, **kwargs):
        required = {"Amount", "BasketID", "Error", "Sig"}
        if not required.issubset(set(request.GET.keys())):
            return HttpResponse("Bad arguments", status=400)
        pubkey: RSAPublicKey = load_pem_public_key(
            settings.SITH_EBOUTIC_PUB_KEY.encode("utf-8")
        )
        signature = base64.b64decode(request.GET["Sig"])
        try:
            data = "&".join(request.META["QUERY_STRING"].split("&")[:-1])
            pubkey.verify(signature, data.encode("utf-8"), PKCS1v15(), SHA1())
        except InvalidSignature:
            return HttpResponse("Bad signature", status=400)
        # Payment authorized:
        # * 'Error' is '00000'
        # * 'Auto' is in the request
        if request.GET["Error"] == "00000" and "Auto" in request.GET:
            try:
                with transaction.atomic():
                    b = (
                        Basket.objects.select_for_update()
                        .filter(id=request.GET["BasketID"])
                        .first()
                    )
                    if b is None:
                        raise SuspiciousOperation("Basket does not exists")
                    if int(b.total * 100) != int(request.GET["Amount"]):
                        raise SuspiciousOperation(
                            "Basket total and amount do not match"
                        )
                    i = Invoice()
                    i.user = b.user
                    i.payment_method = "CARD"
                    i.save()
                    for it in b.items.all():
                        InvoiceItem(
                            invoice=i,
                            product_id=it.product_id,
                            product_name=it.product_name,
                            type_id=it.type_id,
                            product_unit_price=it.product_unit_price,
                            quantity=it.quantity,
                        ).save()
                    i.validate()
                    b.delete()
            except Exception as e:
                return HttpResponse(
                    "Basket processing failed with error: " + repr(e), status=500
                )
            return HttpResponse("Payment successful", status=200)
        else:
            return HttpResponse(
                "Payment failed with error: " + request.GET["Error"], status=202
            )
