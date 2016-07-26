from collections import OrderedDict
from datetime import datetime
import hmac
import base64
from OpenSSL import crypto

from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView, View
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db import transaction, DataError
from django.utils.translation import ugettext as _
from django.conf import settings

from counter.models import Product, Customer, Counter
from eboutic.models import Basket, Invoice, BasketItem, InvoiceItem

# Create your views here.
class EbouticMain(TemplateView):
    template_name = 'eboutic/eboutic_main.jinja'

    def sum_basket(request):
        total = 0
        for pid,infos in request.session['basket'].items():
            total += infos['price'] * infos['qty']
        return total / 100

    def get(self, request, *args, **kwargs):
        if 'basket' not in request.session.keys(): # Init the basket session entry
            request.session['basket'] = {}
            request.session['basket_total'] = 0
        return super(EbouticMain, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'basket' not in request.session.keys(): # Init the basket session entry
            request.session['basket'] = {}
            request.session['basket_total'] = 0
        if 'add_product' in request.POST['action']:
            self.add_product(request)
        elif 'del_product' in request.POST['action']:
            self.del_product(request)
        elif 'pay' in request.POST['action']:
            self.ask_payment(request)
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_price(self, pid):
        return Product.objects.filter(pk=pid).first().selling_price

    def add_product(self, request, q = 1, p=None):
        """ Add a product to the basket """
        pid = p or request.POST['product_id']
        pid = str(pid)
        price = self.get_price(pid)
        total = EbouticMain.sum_basket(request)
        if pid in request.session['basket']:
            request.session['basket'][pid]['qty'] += q
        else:
            request.session['basket'][pid] = {'qty': q, 'price': int(price*100)}
        request.session.modified = True
        return True

    def del_product(self, request):
        """ Delete a product from the basket """
        pid = str(request.POST['product_id'])
        if pid in request.session['basket']:
            request.session['basket'][pid]['qty'] -= 1
            if request.session['basket'][pid]['qty'] <= 0:
                del request.session['basket'][pid]
        else:
            request.session['basket'][pid] = 0
        request.session.modified = True

    def get_context_data(self, **kwargs):
        kwargs = super(EbouticMain, self).get_context_data(**kwargs)
        kwargs['basket_total'] = EbouticMain.sum_basket(self.request)
        kwargs['eboutic'] = Counter.objects.filter(type="EBOUTIC").first()
        return kwargs

class EbouticCommand(TemplateView):
    template_name = 'eboutic/eboutic_makecommand.jinja'

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))

    def post(self, request, *args, **kwargs):
        if 'basket' not in request.session.keys():
            return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
        if self.make_basket(request):
            kwargs['basket'] = self.basket
        return self.render_to_response(self.get_context_data(**kwargs))

    def make_basket(self, request):
        b = None
        if 'basket_id' in request.session.keys():
            b = Basket.objects.filter(id=request.session['basket_id']).first()
        if b is None:
            b = Basket()
        b.user = request.user
        b.save()
        request.session['basket_id'] = b.id
        request.session.modified = True
        b.items.all().delete()
        for pid,infos in request.session['basket'].items():
            BasketItem(basket=b, product_name=Product.objects.filter(id=int(pid)).first().name,
                    quantity=infos['qty'], product_unit_price=infos['price']/100).save()
        self.basket = b
        return True

    def get_context_data(self, **kwargs):
        kwargs = super(EbouticCommand, self).get_context_data(**kwargs)
        kwargs['et_request'] = OrderedDict()
        kwargs['et_request']['PBX_SITE'] = settings.SITH_EBOUTIC_PBX_SITE
        kwargs['et_request']['PBX_RANG'] = settings.SITH_EBOUTIC_PBX_RANG
        kwargs['et_request']['PBX_IDENTIFIANT'] = settings.SITH_EBOUTIC_PBX_IDENTIFIANT
        kwargs['et_request']['PBX_TOTAL'] = int(self.basket.get_total()*100)
        kwargs['et_request']['PBX_DEVISE'] = 978 # This is Euro. ET support only this value anyway
        kwargs['et_request']['PBX_CMD'] = "CMD_"+str(self.basket.id)
        kwargs['et_request']['PBX_PORTEUR'] = self.basket.user.email
        kwargs['et_request']['PBX_RETOUR'] = "Amount:M;BasketID:R;Auto:A;Error:E;Sig:K"
        kwargs['et_request']['PBX_HASH'] = "SHA512"
        kwargs['et_request']['PBX_TIME'] = str(datetime.now().replace(microsecond=0).isoformat('T'))
        kwargs['et_request']['PBX_HMAC'] = hmac.new(settings.SITH_EBOUTIC_HMAC_KEY,
                bytes("&".join(["%s=%s"%(k,v) for k,v in kwargs['et_request'].items()]), 'utf-8'),
                "sha512").hexdigest().upper()
        return kwargs

class EbouticPayWithSith(TemplateView):
    template_name = 'eboutic/eboutic_payment_result.jinja'

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                if 'basket_id' not in request.session.keys() or not request.user.is_authenticated():
                    return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
                b = Basket.objects.filter(id=request.session['basket_id']).first()
                if b is None:
                    return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
                c = Customer.objects.filter(user__id=b.user.id).first()
                if c is None:
                    return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
                kwargs['not_enough'] = True
                if c.amount < b.get_total():
                    raise DataError(_("You do not have enough money to buy the basket"))
                else:
                    i = Invoice()
                    i.user = b.user
                    i.payment_method = "SITH_ACCOUNT"
                    i.save()
                    for it in b.items.all():
                        InvoiceItem(invoice=i, product_name=it.product_name,
                                product_unit_price=it.product_unit_price, quantity=it.quantity).save()
                    i.validate()
                    kwargs['not_enough'] = False
                    request.session.pop('basket_id', None)
                    request.session.pop('basket', None)
        except DataError as e:
                kwargs['not_enough'] = True
        return self.render_to_response(self.get_context_data(**kwargs))

class EtransactionAutoAnswer(View):
    def get(self, request, *args, **kwargs):
        if (not 'Amount' in request.GET.keys() or
            not 'BasketID' in request.GET.keys() or
            not 'Auto' in request.GET.keys() or
            not 'Error' in request.GET.keys() or
            not 'Sig' in request.GET.keys()):
            return HttpResponse("Bad arguments", status=400)
        key = crypto.load_publickey(crypto.FILETYPE_PEM, settings.SITH_EBOUTIC_PUB_KEY)
        cert = crypto.X509()
        cert.set_pubkey(key)
        sig = base64.b64decode(request.GET['Sig'])
        try:
            crypto.verify(cert, sig, '&'.join(request.META['QUERY_STRING'].split('&')[:-1]), "sha1")
        except:
            return HttpResponse("Bad signature", status=400)
        if request.GET['Error'] == "00000":
            with transaction.atomic():
                b = Basket.objects.filter(id=request.GET['BasketID']).first()
                if b is None:
                    return HttpResponse("Basket does not exists", status=400)
                i = Invoice()
                i.user = b.user
                i.payment_method = "CREDIT_CARD"
                i.save()
                for it in b.items.all():
                    InvoiceItem(invoice=i, product_name=it.product_name,
                            product_unit_price=it.product_unit_price, quantity=it.quantity).save()
                i.validate()
            return HttpResponse("Payment validated")
        else:
            return HttpResponse("Payment failed with error: "+request.GET['Error'])
