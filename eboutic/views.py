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
from datetime import datetime
from typing import TYPE_CHECKING

import sentry_sdk
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.core.exceptions import SuspiciousOperation
from django.db import DatabaseError, transaction
from django.db.utils import cached_property
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView, UpdateView, View
from django_countries.fields import Country

from core.views.mixins import FragmentMixin, UseFragmentsMixin
from counter.forms import BillingInfoForm
from counter.models import BillingInfo, Counter, Customer, Product
from eboutic.forms import BasketForm
from eboutic.models import (
    Basket,
    BasketItem,
    BillingInfoState,
    Invoice,
    InvoiceItem,
    get_eboutic_products,
)
from eboutic.schemas import PurchaseItemList, PurchaseItemSchema

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
    from django.utils.html import SafeString


@login_required
@require_GET
def eboutic_main(request: HttpRequest) -> HttpResponse:
    """Main view of the eboutic application.

    Return an Http response whose content is of type text/html.
    The latter represents the page from which a user can see
    the catalogue of products that he can buy and fill
    his shopping cart.

    The purchasable products are those of the eboutic which
    belong to a category of products of a product category
    (orphan products are inaccessible).

    If the session contains a key-value pair that associates "errors"
    with a list of strings, this pair is removed from the session
    and its value displayed to the user when the page is rendered.
    """
    errors = request.session.pop("errors", None)
    products = get_eboutic_products(request.user)
    context = {
        "errors": errors,
        "products": products,
        "customer_amount": request.user.account_balance,
    }
    return render(request, "eboutic/eboutic_main.jinja", context)


@require_GET
@login_required
def payment_result(request, result: str) -> HttpResponse:
    context = {"success": result == "success"}
    return render(request, "eboutic/eboutic_payment_result.jinja", context)


class BillingInfoFormFragment(LoginRequiredMixin, FragmentMixin, UpdateView):
    """Update billing info"""

    model = BillingInfo
    form_class = BillingInfoForm
    template_name = "eboutic/eboutic_billing_info.jinja"

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
        kwargs["action"] = reverse("eboutic:billing_infos")
        kwargs["BillingInfoState"] = BillingInfoState
        kwargs["billing_infos_state"] = BillingInfoState.from_model(self.object)
        return kwargs

    def get_success_url(self, **kwargs):
        return self.request.path


class EbouticCommand(LoginRequiredMixin, UseFragmentsMixin, TemplateView):
    template_name = "eboutic/eboutic_makecommand.jinja"
    basket: Basket
    fragments = {
        "billing_infos_form": BillingInfoFormFragment,
    }

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        return redirect("eboutic:main")

    def get(self, request: HttpRequest, *args, **kwargs):
        form = BasketForm(request)
        if not form.is_valid():
            request.session["errors"] = form.errors
            request.session.modified = True
            res = redirect("eboutic:main")
            res.set_cookie(
                "basket_items",
                PurchaseItemList.dump_json(form.cleaned_data, by_alias=True).decode(),
                path="/eboutic",
            )
            return res
        basket = Basket.from_session(request.session)
        if basket is not None:
            basket.items.all().delete()
        else:
            basket = Basket.objects.create(user=request.user)
            request.session["basket_id"] = basket.id
            request.session.modified = True

        items: list[PurchaseItemSchema] = form.cleaned_data
        pks = {item.product_id for item in items}
        products = {p.pk: p for p in Product.objects.filter(pk__in=pks)}
        db_items = []
        for pk in pks:
            quantity = sum(i.quantity for i in items if i.product_id == pk)
            db_items.append(BasketItem.from_product(products[pk], quantity, basket))
        BasketItem.objects.bulk_create(db_items)
        self.basket = basket
        return super().get(request)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if hasattr(self.request.user, "customer"):
            customer = self.request.user.customer
            kwargs["customer_amount"] = customer.amount
        else:
            kwargs["customer_amount"] = None
        kwargs["basket"] = self.basket
        kwargs["billing_infos"] = {}
        with contextlib.suppress(BillingInfo.DoesNotExist):
            kwargs["billing_infos"] = dict(self.basket.get_e_transaction_data())
        return kwargs


@login_required
@require_POST
def pay_with_sith(request):
    basket = Basket.from_session(request.session)
    refilling = settings.SITH_COUNTER_PRODUCTTYPE_REFILLING
    if basket is None or basket.items.filter(type_id=refilling).exists():
        return redirect("eboutic:main")
    c = Customer.objects.filter(user__id=basket.user_id).first()
    if c is None:
        return redirect("eboutic:main")
    if c.amount < basket.total:
        res = redirect("eboutic:payment_result", "failure")
        res.delete_cookie("basket_items", "/eboutic")
        return res
    eboutic = Counter.objects.get(type="EBOUTIC")
    sales = basket.generate_sales(eboutic, c.user, "SITH_ACCOUNT")
    try:
        with transaction.atomic():
            # Selling.save has some important business logic in it.
            # Do not bulk_create this
            for sale in sales:
                sale.save()
            basket.delete()
        request.session.pop("basket_id", None)
        res = redirect("eboutic:payment_result", "success")
    except DatabaseError as e:
        with sentry_sdk.push_scope() as scope:
            scope.user = {"username": request.user.username}
            scope.set_extra("someVariable", e.__repr__())
            sentry_sdk.capture_message(
                f"Erreur le {datetime.now()} dans eboutic.pay_with_sith"
            )
        res = redirect("eboutic:payment_result", "failure")
    res.delete_cookie("basket_items", "/eboutic")
    return res


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
