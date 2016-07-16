from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.utils import timezone
from django import forms
from django.utils.translation import ugettext_lazy as _

import re

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from subscription.models import Subscriber
from counter.models import Counter, Customer, Product, Selling, Refilling

class GetUserForm(forms.Form):
    """
    The Form class aims at providing a valid user_id field in its cleaned data, in order to pass it to some view,
    reverse function, or any other use.

    The Form implements a nice JS widget allowing the user to type a customer account id, or search the database with
    some nickname, first name, or last name (TODO)
    """
    code = forms.CharField(label="Code", max_length=10, required=False)
    id = forms.IntegerField(label="ID", required=False)
# TODO: add a nice JS widget to search for users

    def as_p(self):
        self.fields['code'].widget.attrs['autofocus'] = True
        return super(GetUserForm, self).as_p()

    def clean(self):
        cleaned_data = super(GetUserForm, self).clean()
        user = None
        if cleaned_data['code'] != "":
            user = Customer.objects.filter(account_id=cleaned_data['code']).first()
        elif cleaned_data['id'] is not None:
            user = Customer.objects.filter(user=cleaned_data['id']).first()
        if user is None:
            raise forms.ValidationError("User not found")
        cleaned_data['user_id'] = user.user.id
        return cleaned_data

class CounterMain(DetailView, ProcessFormView, FormMixin):
    """
    The public (barman) view
    """
    model = Counter
    template_name = 'counter/counter_main.jinja'
    pk_url_kwarg = "counter_id"
    form_class = GetUserForm # Form to enter a client code and get the corresponding user id

    def get_context_data(self, **kwargs):
        """
        We handle here the login form for the barman

        Also handle the timeout
        """
        if self.request.method == 'POST':
            self.object = self.get_object()
        kwargs = super(CounterMain, self).get_context_data(**kwargs)
# TODO: make some checks on the counter type, in order not to make the AuthenticationForm if there is no need to
        kwargs['login_form'] = AuthenticationForm()
        kwargs['login_form'].fields['username'].widget.attrs['autofocus'] = True
        kwargs['form'] = self.get_form()
        kwargs['barmen'] = Counter.get_barmen_list(self.object.id)
        if 'last_basket' in self.request.session.keys():
            kwargs['last_basket'] = self.request.session.pop('last_basket')
            kwargs['last_customer'] = self.request.session.pop('last_customer')
            kwargs['last_total'] = self.request.session.pop('last_total')
            kwargs['new_customer_amount'] = self.request.session.pop('new_customer_amount')
        return kwargs

    def form_valid(self, form):
        """
        We handle here the redirection, passing the user id of the asked customer
        """
        self.kwargs['user_id'] = form.cleaned_data['user_id']
        return super(CounterMain, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('counter:click', args=self.args, kwargs=self.kwargs)

class CounterClick(DetailView):
    """
    The click view
    This is a detail view not to have to worry about loading the counter
    Everything is made by hand in the post method
    """
    model = Counter
    template_name = 'counter/counter_click.jinja'
    pk_url_kwarg = "counter_id"

    def get(self, request, *args, **kwargs):
        """Simple get view"""
        self.customer = Customer.objects.filter(user__id=self.kwargs['user_id']).first()
        if 'basket' not in request.session.keys(): # Init the basket session entry
            request.session['basket'] = {}
            request.session['basket_total'] = 0
        request.session['not_enough'] = False
        ret = super(CounterClick, self).get(request, *args, **kwargs)
        if len(Counter.get_barmen_list(self.object.id)) < 1: # Check that at least one barman is logged in
            return self.cancel(request) # Otherwise, go to main view
        return ret

    def post(self, request, *args, **kwargs):
        """ Handle the many possibilities of the post request """
        self.object = self.get_object()
        self.customer = Customer.objects.filter(user__id=self.kwargs['user_id']).first()
        if len(Counter.get_barmen_list(self.object.id)) < 1: # Check that at least one barman is logged in
            return self.cancel(request)
        if 'basket' not in request.session.keys():
            request.session['basket'] = {}
            request.session['basket_total'] = 0
        request.session['not_enough'] = False

        if 'add_product' in request.POST['action']:
            self.add_product(request)
        elif 'del_product' in request.POST['action']:
            self.del_product(request)
        elif 'refill' in request.POST['action']:
            self.refill(request)
        elif 'code' in request.POST['action']:
            return self.parse_code(request)
        elif 'cancel' in request.POST['action']:
            return self.cancel(request)
        elif 'finish' in request.POST['action']:
            return self.finish(request)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def is_barman_price(self):
        if self.customer.user.id in [s.id for s in Counter.get_barmen_list(self.object.id)]:
            return True
        else:
            return False

    def get_price(self, pid):
        p = Product.objects.filter(pk=pid).first()
        if self.is_barman_price():
            price = p.special_selling_price
        else:
            price = p.selling_price
        return price

    def sum_basket(self, request):
        total = 0
        for pid,infos in request.session['basket'].items():
            total += infos['price'] * infos['qty']
        return total / 100

    def add_product(self, request, q = 1, p=None):
        """ Add a product to the basket """
        pid = p or request.POST['product_id']
        pid = str(pid)
        price = self.get_price(pid)
        total = self.sum_basket(request)
        if self.customer.amount < (total + q*float(price)):
            request.session['not_enough'] = True
            return False
        if pid in request.session['basket']:
            request.session['basket'][pid]['qty'] += q
        else:
            request.session['basket'][pid] = {'qty': q, 'price': int(price*100)}
        request.session['not_enough'] = False
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

    def parse_code(self, request):
        """Parse the string entered by the barman"""
        string = str(request.POST['code']).upper()
        if string == _("FIN"):
            return self.finish(request)
        elif string == _("ANN"):
            return self.cancel(request)
        regex = re.compile(r"^((?P<nb>[0-9]+)X)?(?P<code>[A-Z0-9]+)$")
        m = regex.match(string)
        if m is not None:
            nb = m.group('nb')
            code = m.group('code')
            if nb is None:
                nb = 1
            else:
                nb = int(nb)
            p = Product.objects.filter(code=code).first()
            if p is not None:
                while nb > 0 and not self.add_product(request, nb, p.id):
                    nb -= 1
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def finish(self, request):
        """ Finish the click session, and validate the basket """
        if self.is_barman_price():
            seller = self.customer.user
        else:
            seller = Counter.get_random_barman(self.object.id)
        request.session['last_basket'] = []
        for pid,infos in request.session['basket'].items():
            # This duplicates code for DB optimization (prevent to load many times the same object)
            p = Product.objects.filter(pk=pid).first()
            if self.is_barman_price():
                uprice = p.special_selling_price
            else:
                uprice = p.selling_price
            request.session['last_basket'].append("%d x %s" % (infos['qty'], p.name))
            s = Selling(product=p, counter=self.object, unit_price=uprice,
                   quantity=infos['qty'], seller=seller, customer=self.customer)
            s.save()
        request.session['last_customer'] = self.customer.user.get_display_name()
        request.session['last_total'] = "%0.2f" % self.sum_basket(request)
        request.session['new_customer_amount'] = str(self.customer.amount)
        del request.session['basket']
        request.session.modified = True
        kwargs = {
                'counter_id': self.object.id,
                }
        return HttpResponseRedirect(reverse_lazy('counter:details', args=self.args, kwargs=kwargs))

    def cancel(self, request):
        """ Cancel the click session """
        kwargs = {'counter_id': self.object.id}
        request.session.pop('basket', None)
        return HttpResponseRedirect(reverse_lazy('counter:details', args=self.args, kwargs=kwargs))

    def refill(self, request):
        """Refill the customer's account"""
        if self.is_barman_price():
            operator = self.customer.user
        else:
            operator = Counter.get_random_barman(self.object.id)
        amount = float(request.POST['amount'])
        s = Refilling(counter=self.object, operator=operator, customer=self.customer,
                amount=amount, payment_method="cash")
        s.save()

    def get_context_data(self, **kwargs):
        """ Add customer to the context """
        kwargs = super(CounterClick, self).get_context_data(**kwargs)
        kwargs['customer'] = self.customer
        kwargs['basket_total'] = self.sum_basket(self.request)
        return kwargs

class CounterLogin(RedirectView):
    """
    Handle the login of a barman

    Logged barmen are stored in the class-wide variable 'barmen_session', in the Counter model
    """
    permanent = False
    def post(self, request, *args, **kwargs):
        """
        Register the logged user as barman for this counter
        """
        self.counter_id = kwargs['counter_id']
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = Subscriber.objects.filter(username=form.cleaned_data['username']).first()
            if self.counter_id not in Counter.barmen_session.keys():
                Counter.barmen_session[self.counter_id] = {'users': {user.id}, 'time': timezone.now()}
            else:
                Counter.barmen_session[self.counter_id]['users'].add(user.id)
        else:
            print("Error logging the barman") # TODO handle that nicely
        return super(CounterLogin, self).post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('counter:details', args=args, kwargs=kwargs)

class CounterLogout(RedirectView):
    permanent = False
    def post(self, request, *args, **kwargs):
        """
        Unregister the user from the barman
        """
        self.counter_id = kwargs['counter_id']
        Counter.barmen_session[str(self.counter_id)]['users'].remove(int(request.POST['user_id']))
        return super(CounterLogout, self).post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('counter:details', args=args, kwargs=kwargs)

## Counter admin views

class CounterListView(CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = Counter
    template_name = 'counter/counter_list.jinja'

class CounterEditView(CanEditMixin, UpdateView):
    """
    Edit a counter's main informations (for the counter's admin)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    pk_url_kwarg = "counter_id"
    template_name = 'counter/counter_edit.jinja'

class CounterCreateView(CanEditMixin, CreateView):
    """
    Create a counter (for the admins)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    template_name = 'counter/counter_edit.jinja'

class CounterDeleteView(CanEditMixin, DeleteView):
    """
    Delete a counter (for the admins)
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('counter:admin_list')


