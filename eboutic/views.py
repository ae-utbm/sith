from django.shortcuts import render

from django.core.urlresolvers import reverse_lazy
from eboutic.models import Eboutic
from django.views.generic import TemplateView, View
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db import transaction, DataError
from django.utils.translation import ugettext as _

from counter.models import Product, Customer
from eboutic.models import Basket, Invoice, Eboutic, BasketItem, InvoiceItem

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
        kwargs['eboutic'] = Eboutic.objects.filter(type="EBOUTIC").first()
        return kwargs

class EbouticCommand(TemplateView):
    template_name = 'eboutic/eboutic_makecommand.jinja'

    def post(self, request, *args, **kwargs):
        if 'basket' not in request.session.keys():
            return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
        if 'ask_payment' in request.POST['action']:
            if self.ask_payment(request):
                kwargs['basket'] = self.basket
        return self.render_to_response(self.get_context_data(**kwargs))

    def ask_payment(self, request):
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

class EbouticPayWithSith(TemplateView):
    template_name = 'eboutic/eboutic_payment_result.jinja'

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                if 'basket_id' not in request.session.keys() or not request.user.is_authenticated():
                    return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
                b = Basket.objects.filter(id=request.session['basket_id']).first()
                c = Customer.objects.filter(user__id=request.user.id).first()
                if b is None or c is None:
                    return HttpResponseRedirect(reverse_lazy('eboutic:main', args=self.args, kwargs=kwargs))
                kwargs['not_enough'] = True
                if c.amount < b.get_total():
                    raise DataError(_("You have not enough money to buy the basket"))
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
    def get(self, request, *args, **kwargs): # TODO implement CA's API
        return HttpResponse()
