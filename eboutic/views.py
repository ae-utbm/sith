# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from collections import OrderedDict
from datetime import datetime
import hmac
import base64
from OpenSSL import crypto

from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView, View
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import SuspiciousOperation
from django.db import transaction, DataError
from django.utils.translation import ugettext as _
from django.conf import settings

from counter.models import Customer, Counter, ProductType, Selling
from eboutic.models import Basket, Invoice, InvoiceItem


class EbouticMain(TemplateView):
    template_name = "eboutic/eboutic_main.jinja"

    def make_basket(self, request):
        if "basket_id" not in request.session.keys():  # Init the basket session entry
            self.basket = Basket(user=request.user)
            self.basket.save()
        else:
            self.basket = Basket.objects.filter(id=request.session["basket_id"]).first()
            if self.basket is None:
                self.basket = Basket(user=request.user)
                self.basket.save()
        request.session["basket_id"] = self.basket.id
        request.session.modified = True

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse_lazy("core:login", args=self.args, kwargs=kwargs)
                + "?next="
                + request.path
            )
        self.object = Counter.objects.filter(type="EBOUTIC").first()
        self.make_basket(request)
        return super(EbouticMain, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse_lazy("core:login", args=self.args, kwargs=kwargs)
                + "?next="
                + request.path
            )
        self.object = Counter.objects.filter(type="EBOUTIC").first()
        self.make_basket(request)
        if "add_product" in request.POST["action"]:
            self.add_product(request)
        elif "del_product" in request.POST["action"]:
            self.del_product(request)
        return self.render_to_response(self.get_context_data(**kwargs))

    def add_product(self, request):
        """ Add a product to the basket """
        try:
            p = self.object.products.filter(id=int(request.POST["product_id"])).first()
            if not p.buying_groups.exists():
                self.basket.add_product(p)
            for g in p.buying_groups.all():
                if request.user.is_in_group(g.name):
                    self.basket.add_product(p)
                    break
        except:
            pass

    def del_product(self, request):
        """ Delete a product from the basket """
        try:
            p = self.object.products.filter(id=int(request.POST["product_id"])).first()
            self.basket.del_product(p)
        except:
            pass

    def get_context_data(self, **kwargs):
        kwargs = super(EbouticMain, self).get_context_data(**kwargs)
        kwargs["basket"] = self.basket
        kwargs["eboutic"] = Counter.objects.filter(type="EBOUTIC").first()
        kwargs["categories"] = ProductType.objects.all()
        if not self.request.user.was_subscribed:
            kwargs["categories"] = kwargs["categories"].exclude(
                id=settings.SITH_PRODUCTTYPE_SUBSCRIPTION
            )
        return kwargs


class EbouticCommand(TemplateView):
    template_name = "eboutic/eboutic_makecommand.jinja"

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse_lazy("core:login", args=self.args, kwargs=kwargs)
                + "?next="
                + request.path
            )
        return HttpResponseRedirect(
            reverse_lazy("eboutic:main", args=self.args, kwargs=kwargs)
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse_lazy("core:login", args=self.args, kwargs=kwargs)
                + "?next="
                + request.path
            )
        if "basket_id" not in request.session.keys():
            return HttpResponseRedirect(
                reverse_lazy("eboutic:main", args=self.args, kwargs=kwargs)
            )
        self.basket = Basket.objects.filter(id=request.session["basket_id"]).first()
        if self.basket is None:
            return HttpResponseRedirect(
                reverse_lazy("eboutic:main", args=self.args, kwargs=kwargs)
            )
        else:
            kwargs["basket"] = self.basket
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        kwargs = super(EbouticCommand, self).get_context_data(**kwargs)
        kwargs["et_request"] = OrderedDict()
        kwargs["et_request"]["PBX_SITE"] = settings.SITH_EBOUTIC_PBX_SITE
        kwargs["et_request"]["PBX_RANG"] = settings.SITH_EBOUTIC_PBX_RANG
        kwargs["et_request"]["PBX_IDENTIFIANT"] = settings.SITH_EBOUTIC_PBX_IDENTIFIANT
        kwargs["et_request"]["PBX_TOTAL"] = int(self.basket.get_total() * 100)
        kwargs["et_request"][
            "PBX_DEVISE"
        ] = 978  # This is Euro. ET support only this value anyway
        kwargs["et_request"]["PBX_CMD"] = self.basket.id
        kwargs["et_request"]["PBX_PORTEUR"] = self.basket.user.email
        kwargs["et_request"]["PBX_RETOUR"] = "Amount:M;BasketID:R;Auto:A;Error:E;Sig:K"
        kwargs["et_request"]["PBX_HASH"] = "SHA512"
        kwargs["et_request"]["PBX_TYPEPAIEMENT"] = "CARTE"
        kwargs["et_request"]["PBX_TYPECARTE"] = "CB"
        kwargs["et_request"]["PBX_TIME"] = str(
            datetime.now().replace(microsecond=0).isoformat("T")
        )
        kwargs["et_request"]["PBX_HMAC"] = (
            hmac.new(
                settings.SITH_EBOUTIC_HMAC_KEY,
                bytes(
                    "&".join(
                        ["%s=%s" % (k, v) for k, v in kwargs["et_request"].items()]
                    ),
                    "utf-8",
                ),
                "sha512",
            )
            .hexdigest()
            .upper()
        )
        return kwargs


class EbouticPayWithSith(TemplateView):
    template_name = "eboutic/eboutic_payment_result.jinja"

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                if (
                    "basket_id" not in request.session.keys()
                    or not request.user.is_authenticated()
                ):
                    return HttpResponseRedirect(
                        reverse_lazy("eboutic:main", args=self.args, kwargs=kwargs)
                    )
                b = Basket.objects.filter(id=request.session["basket_id"]).first()
                if (
                    b is None
                    or b.items.filter(
                        type_id=settings.SITH_COUNTER_PRODUCTTYPE_REFILLING
                    ).exists()
                ):
                    return HttpResponseRedirect(
                        reverse_lazy("eboutic:main", args=self.args, kwargs=kwargs)
                    )
                c = Customer.objects.filter(user__id=b.user.id).first()
                if c is None:
                    return HttpResponseRedirect(
                        reverse_lazy("eboutic:main", args=self.args, kwargs=kwargs)
                    )
                kwargs["not_enough"] = True
                if c.amount < b.get_total():
                    raise DataError(_("You do not have enough money to buy the basket"))
                else:
                    eboutic = Counter.objects.filter(type="EBOUTIC").first()
                    for it in b.items.all():
                        product = eboutic.products.filter(id=it.product_id).first()
                        Selling(
                            label=it.product_name,
                            counter=eboutic,
                            club=product.club,
                            product=product,
                            seller=c.user,
                            customer=c,
                            unit_price=it.product_unit_price,
                            quantity=it.quantity,
                            payment_method="SITH_ACCOUNT",
                        ).save()
                    b.delete()
                    kwargs["not_enough"] = False
                    request.session.pop("basket_id", None)
        except DataError as e:
            kwargs["not_enough"] = True
        return self.render_to_response(self.get_context_data(**kwargs))


class EtransactionAutoAnswer(View):
    def get(self, request, *args, **kwargs):
        if (
            not "Amount" in request.GET.keys()
            or not "BasketID" in request.GET.keys()
            or not "Auto" in request.GET.keys()
            or not "Error" in request.GET.keys()
            or not "Sig" in request.GET.keys()
        ):
            return HttpResponse("Bad arguments", status=400)
        key = crypto.load_publickey(crypto.FILETYPE_PEM, settings.SITH_EBOUTIC_PUB_KEY)
        cert = crypto.X509()
        cert.set_pubkey(key)
        sig = base64.b64decode(request.GET["Sig"])
        try:
            crypto.verify(
                cert,
                sig,
                "&".join(request.META["QUERY_STRING"].split("&")[:-1]),
                "sha1",
            )
        except:
            return HttpResponse("Bad signature", status=400)
        if request.GET["Error"] == "00000":
            try:
                with transaction.atomic():
                    b = (
                        Basket.objects.select_for_update()
                        .filter(id=request.GET["BasketID"])
                        .first()
                    )
                    if b is None:
                        raise SuspiciousOperation("Basket does not exists")
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
                return HttpResponse("Payment failed with error: " + repr(e), status=400)
            return HttpResponse()
        else:
            return HttpResponse(
                "Payment failed with error: " + request.GET["Error"], status=400
            )
