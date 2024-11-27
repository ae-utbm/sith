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
import re
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from django.core.exceptions import PermissionDenied
from django.db import DataError, transaction
from django.db.models import F
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from core.views import CanViewMixin
from counter.forms import NFCCardForm, RefillForm
from counter.models import Counter, Customer, Product, Selling, StudentCard

if TYPE_CHECKING:
    from core.models import User


class CounterClick(CounterTabsMixin, CanViewMixin, DetailView):
    """The click view
    This is a detail view not to have to worry about loading the counter
    Everything is made by hand in the post method.
    """

    model = Counter
    queryset = Counter.objects.annotate_is_open()
    template_name = "counter/counter_click.jinja"
    pk_url_kwarg = "counter_id"
    current_tab = "counter"

    def render_to_response(self, *args, **kwargs):
        if self.is_ajax(self.request):
            response = {"errors": []}
            status = HTTPStatus.OK

            if self.request.session["too_young"]:
                response["errors"].append(_("Too young for that product"))
                status = HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS
            if self.request.session["not_allowed"]:
                response["errors"].append(_("Not allowed for that product"))
                status = HTTPStatus.FORBIDDEN
            if self.request.session["no_age"]:
                response["errors"].append(_("No date of birth provided"))
                status = HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS
            if self.request.session["not_enough"]:
                response["errors"].append(_("Not enough money"))
                status = HTTPStatus.PAYMENT_REQUIRED

            if len(response["errors"]) > 1:
                status = HTTPStatus.BAD_REQUEST

            response["basket"] = self.request.session["basket"]

            return JsonResponse(response, status=status)

        else:  # Standard HTML page
            return super().render_to_response(*args, **kwargs)

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
            return redirect(obj)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Simple get view."""
        if "basket" not in request.session:  # Init the basket session entry
            request.session["basket"] = {}
            request.session["basket_total"] = 0
        request.session["not_enough"] = False  # Reset every variable
        request.session["too_young"] = False
        request.session["not_allowed"] = False
        request.session["no_age"] = False
        self.refill_form = None
        ret = super().get(request, *args, **kwargs)
        if (self.object.type != "BAR" and not request.user.is_authenticated) or (
            self.object.type == "BAR" and len(self.object.barmen_list) == 0
        ):  # Check that at least one barman is logged in
            ret = self.cancel(request)  # Otherwise, go to main view
        return ret

    def post(self, request, *args, **kwargs):
        """Handle the many possibilities of the post request."""
        self.object = self.get_object()
        self.refill_form = None
        if (self.object.type != "BAR" and not request.user.is_authenticated) or (
            self.object.type == "BAR" and len(self.object.barmen_list) < 1
        ):  # Check that at least one barman is logged in
            return self.cancel(request)
        if self.object.type == "BAR" and not (
            "counter_token" in self.request.session
            and self.request.session["counter_token"] == self.object.token
        ):  # Also check the token to avoid the bar to be stolen
            return HttpResponseRedirect(
                reverse_lazy(
                    "counter:details",
                    args=self.args,
                    kwargs={"counter_id": self.object.id},
                )
                + "?bad_location"
            )
        if "basket" not in request.session:
            request.session["basket"] = {}
            request.session["basket_total"] = 0
        request.session["not_enough"] = False  # Reset every variable
        request.session["too_young"] = False
        request.session["not_allowed"] = False
        request.session["no_age"] = False
        request.session["not_valid_student_card_uid"] = False
        if self.object.type != "BAR":
            self.operator = request.user
        elif self.customer_is_barman():
            self.operator = self.customer.user
        else:
            self.operator = self.object.get_random_barman()
        action = self.request.POST.get("action", None)
        if action is None:
            action = parse_qs(request.body.decode()).get("action", [""])[0]
        if action == "add_product":
            self.add_product(request)
        elif action == "add_student_card":
            self.add_student_card(request)
        elif action == "del_product":
            self.del_product(request)
        elif action == "refill":
            self.refill(request)
        elif action == "code":
            return self.parse_code(request)
        elif action == "cancel":
            return self.cancel(request)
        elif action == "finish":
            return self.finish(request)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def customer_is_barman(self) -> bool:
        barmen = self.object.barmen_list
        return self.object.type == "BAR" and self.customer.user in barmen

    def get_product(self, pid):
        return Product.objects.filter(pk=int(pid)).first()

    def get_price(self, pid):
        p = self.get_product(pid)
        if self.customer_is_barman():
            price = p.special_selling_price
        else:
            price = p.selling_price
        return price

    def sum_basket(self, request):
        total = 0
        for infos in request.session["basket"].values():
            total += infos["price"] * infos["qty"]
        return total / 100

    def get_total_quantity_for_pid(self, request, pid):
        pid = str(pid)
        if pid not in request.session["basket"]:
            return 0
        return (
            request.session["basket"][pid]["qty"]
            + request.session["basket"][pid]["bonus_qty"]
        )

    def compute_record_product(self, request, product=None):
        recorded = 0
        basket = request.session["basket"]

        if product:
            if product.is_record_product:
                recorded -= 1
            elif product.is_unrecord_product:
                recorded += 1

        for p in basket:
            bproduct = self.get_product(str(p))
            if bproduct.is_record_product:
                recorded -= basket[p]["qty"]
            elif bproduct.is_unrecord_product:
                recorded += basket[p]["qty"]
        return recorded

    def is_record_product_ok(self, request, product):
        return self.customer.can_record_more(
            self.compute_record_product(request, product)
        )

    @staticmethod
    def is_ajax(request):
        # when using the fetch API, the django request.POST dict is empty
        # this is but a wretched contrivance which strive to replace
        # the deprecated django is_ajax() method
        # and which must be replaced as soon as possible
        # by a proper separation between the api endpoints of the counter
        return len(request.POST) == 0 and len(request.body) != 0

    def add_product(self, request, q=1, p=None):
        """Add a product to the basket
        q is the quantity passed as integer
        p is the product id, passed as an integer.
        """
        pid = p or parse_qs(request.body.decode())["product_id"][0]
        pid = str(pid)
        price = self.get_price(pid)
        total = self.sum_basket(request)
        product: Product = self.get_product(pid)
        user: User = self.customer.user
        buying_groups = list(product.buying_groups.values_list("pk", flat=True))
        can_buy = len(buying_groups) == 0 or any(
            user.is_in_group(pk=group_id) for group_id in buying_groups
        )
        if not can_buy:
            request.session["not_allowed"] = True
            return False
        bq = 0  # Bonus quantity, for trays
        if (
            product.tray
        ):  # Handle the tray to adjust the quantity q to add and the bonus quantity bq
            total_qty_mod_6 = self.get_total_quantity_for_pid(request, pid) % 6
            bq = int((total_qty_mod_6 + q) / 6)  # Integer division
            q -= bq
        if self.customer.amount < (
            total + round(q * float(price), 2)
        ):  # Check for enough money
            request.session["not_enough"] = True
            return False
        if product.is_unrecord_product and not self.is_record_product_ok(
            request, product
        ):
            request.session["not_allowed"] = True
            return False
        if product.limit_age >= 18 and not user.date_of_birth:
            request.session["no_age"] = True
            return False
        if product.limit_age >= 18 and user.is_banned_alcohol:
            request.session["not_allowed"] = True
            return False
        if user.is_banned_counter:
            request.session["not_allowed"] = True
            return False
        if (
            user.date_of_birth and self.customer.user.get_age() < product.limit_age
        ):  # Check if affordable
            request.session["too_young"] = True
            return False
        if pid in request.session["basket"]:  # Add if already in basket
            request.session["basket"][pid]["qty"] += q
            request.session["basket"][pid]["bonus_qty"] += bq
        else:  # or create if not
            request.session["basket"][pid] = {
                "qty": q,
                "price": int(price * 100),
                "bonus_qty": bq,
            }
        request.session.modified = True
        return True

    def add_student_card(self, request):
        """Add a new student card on the customer account."""
        uid = str(request.POST["student_card_uid"])
        if not StudentCard.is_valid(uid):
            request.session["not_valid_student_card_uid"] = True
            return False

        if not (
            self.object.type == "BAR"
            and "counter_token" in request.session
            and request.session["counter_token"] == self.object.token
            and self.object.is_open
        ):
            raise PermissionDenied
        StudentCard(customer=self.customer, uid=uid).save()
        return True

    def del_product(self, request):
        """Delete a product from the basket."""
        pid = parse_qs(request.body.decode())["product_id"][0]
        product = self.get_product(pid)
        if pid in request.session["basket"]:
            if (
                product.tray
                and (self.get_total_quantity_for_pid(request, pid) % 6 == 0)
                and request.session["basket"][pid]["bonus_qty"]
            ):
                request.session["basket"][pid]["bonus_qty"] -= 1
            else:
                request.session["basket"][pid]["qty"] -= 1
            if request.session["basket"][pid]["qty"] <= 0:
                del request.session["basket"][pid]
        request.session.modified = True

    def parse_code(self, request):
        """Parse the string entered by the barman.

        This can be of two forms :
            - `<str>`, where the string is the code of the product
            - `<int>X<str>`, where the integer is the quantity and str the code.
        """
        string = parse_qs(request.body.decode()).get("code", [""])[0].upper()
        if string == "FIN":
            return self.finish(request)
        elif string == "ANN":
            return self.cancel(request)
        regex = re.compile(r"^((?P<nb>[0-9]+)X)?(?P<code>[A-Z0-9]+)$")
        m = regex.match(string)
        if m is not None:
            nb = m.group("nb")
            code = m.group("code")
            nb = int(nb) if nb is not None else 1
            p = self.object.products.filter(code=code).first()
            if p is not None:
                self.add_product(request, nb, p.id)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def finish(self, request):
        """Finish the click session, and validate the basket."""
        with transaction.atomic():
            request.session["last_basket"] = []
            if self.sum_basket(request) > self.customer.amount:
                raise DataError(_("You have not enough money to buy all the basket"))

            for pid, infos in request.session["basket"].items():
                # This duplicates code for DB optimization (prevent to load many times the same object)
                p = Product.objects.filter(pk=pid).first()
                if self.customer_is_barman():
                    uprice = p.special_selling_price
                else:
                    uprice = p.selling_price
                request.session["last_basket"].append(
                    "%d x %s" % (infos["qty"] + infos["bonus_qty"], p.name)
                )
                s = Selling(
                    label=p.name,
                    product=p,
                    club=p.club,
                    counter=self.object,
                    unit_price=uprice,
                    quantity=infos["qty"],
                    seller=self.operator,
                    customer=self.customer,
                )
                s.save()
                if infos["bonus_qty"]:
                    s = Selling(
                        label=p.name + " (Plateau)",
                        product=p,
                        club=p.club,
                        counter=self.object,
                        unit_price=0,
                        quantity=infos["bonus_qty"],
                        seller=self.operator,
                        customer=self.customer,
                    )
                    s.save()
                self.customer.recorded_products -= self.compute_record_product(request)
                self.customer.save()
            request.session["last_customer"] = self.customer.user.get_display_name()
            request.session["last_total"] = "%0.2f" % self.sum_basket(request)
            request.session["new_customer_amount"] = str(self.customer.amount)
            del request.session["basket"]
            request.session.modified = True
            kwargs = {"counter_id": self.object.id}
            return HttpResponseRedirect(
                reverse_lazy("counter:details", args=self.args, kwargs=kwargs)
            )

    def cancel(self, request):
        """Cancel the click session."""
        kwargs = {"counter_id": self.object.id}
        request.session.pop("basket", None)
        return HttpResponseRedirect(
            reverse_lazy("counter:details", args=self.args, kwargs=kwargs)
        )

    def refill(self, request):
        """Refill the customer's account."""
        if not self.object.can_refill():
            raise PermissionDenied
        form = RefillForm(request.POST)
        if form.is_valid():
            form.instance.counter = self.object
            form.instance.operator = self.operator
            form.instance.customer = self.customer
            form.instance.save()
        else:
            self.refill_form = form

    def get_context_data(self, **kwargs):
        """Add customer to the context."""
        kwargs = super().get_context_data(**kwargs)
        products = self.object.products.select_related("product_type")
        if self.customer_is_barman():
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
        kwargs["student_cards"] = self.customer.student_cards.all()
        kwargs["student_card_input"] = NFCCardForm()
        kwargs["basket_total"] = self.sum_basket(self.request)
        kwargs["refill_form"] = self.refill_form or RefillForm()
        kwargs["student_card_max_uid_size"] = StudentCard.UID_SIZE
        kwargs["barmens_can_refill"] = self.object.can_refill()
        return kwargs
