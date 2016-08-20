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
from django.conf import settings
from django.db import DataError, transaction

import re
from datetime import date, timedelta
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField
from ajax_select import make_ajax_form, make_ajax_field

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from core.views.forms import SelectUser
from subscription.models import Subscriber
from subscription.views import get_subscriber
from counter.models import Counter, Customer, Product, Selling, Refilling, ProductType

class GetUserForm(forms.Form):
    """
    The Form class aims at providing a valid user_id field in its cleaned data, in order to pass it to some view,
    reverse function, or any other use.

    The Form implements a nice JS widget allowing the user to type a customer account id, or search the database with
    some nickname, first name, or last name (TODO)
    """
    code = forms.CharField(label="Code", max_length=10, required=False)
    id = AutoCompleteSelectField('users', required=False, label=_("Select user"), help_text=None)

    def as_p(self):
        self.fields['code'].widget.attrs['autofocus'] = True
        return super(GetUserForm, self).as_p()

    def clean(self):
        cleaned_data = super(GetUserForm, self).clean()
        cus = None
        if cleaned_data['code'] != "":
            cus = Customer.objects.filter(account_id=cleaned_data['code']).first()
        elif cleaned_data['id'] is not None:
            cus = Customer.objects.filter(user=cleaned_data['id']).first()
        sub = get_subscriber(cus.user) if cus is not None else None
        if (cus is None or sub is None or not sub.subscriptions.last() or
            (date.today() - sub.subscriptions.last().subscription_end) > timedelta(days=90)):
            raise forms.ValidationError(_("User not found"))
        cleaned_data['user_id'] = cus.user.id
        cleaned_data['user'] = cus.user
        return cleaned_data

class RefillForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Refilling
        fields = ['amount', 'payment_method', 'bank']

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
        """
        if self.request.method == 'POST':
            self.object = self.get_object()
        kwargs = super(CounterMain, self).get_context_data(**kwargs)
        kwargs['login_form'] = AuthenticationForm()
        kwargs['login_form'].fields['username'].widget.attrs['autofocus'] = True
        kwargs['form'] = self.get_form()
        if self.object.type == 'BAR':
            kwargs['barmen'] = self.object.get_barmen_list()
        elif self.request.user.is_authenticated():
            kwargs['barmen'] = [self.request.user]
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
        request.session['too_young'] = False
        self.refill_form = None
        ret = super(CounterClick, self).get(request, *args, **kwargs)
        if ((self.object.type != "BAR" and not request.user.is_authenticated()) or
                (self.object.type == "BAR" and
                len(self.object.get_barmen_list()) < 1)): # Check that at least one barman is logged in
            ret = self.cancel(request) # Otherwise, go to main view
        return ret

    def post(self, request, *args, **kwargs):
        """ Handle the many possibilities of the post request """
        self.object = self.get_object()
        self.customer = Customer.objects.filter(user__id=self.kwargs['user_id']).first()
        self.refill_form = None
        if ((self.object.type != "BAR" and not request.user.is_authenticated()) or
                (self.object.type == "BAR" and
                len(self.object.get_barmen_list()) < 1)): # Check that at least one barman is logged in
            return self.cancel(request)
        if 'basket' not in request.session.keys():
            request.session['basket'] = {}
            request.session['basket_total'] = 0
        request.session['not_enough'] = False
        request.session['too_young'] = False
        if self.object.type != "BAR":
            self.operator = request.user
        elif self.is_barman_price():
            self.operator = self.customer.user
        else:
            self.operator = self.object.get_random_barman()

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
        if self.object.type == "BAR" and self.customer.user.id in [s.id for s in self.object.get_barmen_list()]:
            return True
        else:
            return False

    def get_product(self, pid):
        return Product.objects.filter(pk=int(pid)).first()

    def get_price(self, pid):
        p = self.get_product(pid)
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
        """
        Add a product to the basket
        q is the quantity passed as integer
        p is the product id, passed as an integer
        """
        pid = p or request.POST['product_id']
        pid = str(pid)
        price = self.get_price(pid)
        total = self.sum_basket(request)
        if self.customer.amount < (total + q*float(price)):
            request.session['not_enough'] = True
            return False
        if self.customer.user.get_age() < self.get_product(pid).limit_age:
            request.session['too_young'] = True
            return False
        if pid in request.session['basket']:
            request.session['basket'][pid]['qty'] += q
        else:
            request.session['basket'][pid] = {'qty': q, 'price': int(price*100)}
        request.session['not_enough'] = False # Reset not_enough to save the session
        request.session['too_young'] = False
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
        if string == _("END"):
            return self.finish(request)
        elif string == _("CAN"):
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
            p = self.object.products.filter(code=code).first()
            if p is not None:
                while nb > 0 and not self.add_product(request, nb, p.id):
                    nb -= 1
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def finish(self, request):
        """ Finish the click session, and validate the basket """
        with transaction.atomic():
            request.session['last_basket'] = []
            for pid,infos in request.session['basket'].items():
                # This duplicates code for DB optimization (prevent to load many times the same object)
                p = Product.objects.filter(pk=pid).first()
                if self.is_barman_price():
                    uprice = p.special_selling_price
                else:
                    uprice = p.selling_price
                if uprice * infos['qty'] > self.customer.amount:
                    raise DataError(_("You have not enough money to buy all the basket"))
                request.session['last_basket'].append("%d x %s" % (infos['qty'], p.name))
                s = Selling(label=p.name, product=p, club=p.club, counter=self.object, unit_price=uprice,
                       quantity=infos['qty'], seller=self.operator, customer=self.customer)
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
        form = RefillForm(request.POST)
        if form.is_valid():
            form.instance.counter = self.object
            form.instance.operator = self.operator
            form.instance.customer = self.customer
            form.instance.save()
        else:
            self.refill_form = form

    def get_context_data(self, **kwargs):
        """ Add customer to the context """
        kwargs = super(CounterClick, self).get_context_data(**kwargs)
        kwargs['customer'] = self.customer
        kwargs['basket_total'] = self.sum_basket(self.request)
        kwargs['refill_form'] = self.refill_form or RefillForm()
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
            if user.is_subscribed():
                Counter.add_barman(self.counter_id, user.id)
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
        Counter.del_barman(self.counter_id, request.POST['user_id'])
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

class CounterEditForm(forms.ModelForm):
    class Meta:
        model = Counter
        fields = ['sellers', 'products']
    sellers = make_ajax_field(Counter, 'sellers', 'users', show_help_text=False)
    products = make_ajax_field(Counter, 'products', 'products')

class CounterEditView(CanEditMixin, UpdateView):
    """
    Edit a counter's main informations (for the counter's manager)
    """
    model = Counter
    form_class = CounterEditForm
    pk_url_kwarg = "counter_id"
    template_name = 'counter/counter_edit.jinja'

    def get_success_url(self):
        return reverse_lazy('counter:admin', kwargs={'counter_id': self.object.id})

class CounterEditPropView(CanEditPropMixin, UpdateView):
    """
    Edit a counter's main informations (for the counter's admin)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type'])
    pk_url_kwarg = "counter_id"
    template_name = 'core/edit.jinja'

class CounterCreateView(CanEditMixin, CreateView):
    """
    Create a counter (for the admins)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    template_name = 'core/create.jinja'

class CounterDeleteView(CanEditMixin, DeleteView):
    """
    Delete a counter (for the admins)
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('counter:admin_list')

# Product management

class ProductTypeListView(CanEditPropMixin, ListView):
    """
    A list view for the admins
    """
    model = ProductType
    template_name = 'counter/producttype_list.jinja'

class ProductTypeCreateView(CanCreateMixin, CreateView):
    """
    A create view for the admins
    """
    model = ProductType
    fields = ['name', 'description', 'icon']
    template_name = 'core/create.jinja'

class ProductTypeEditView(CanEditPropMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = ProductType
    template_name = 'core/edit.jinja'
    fields = ['name', 'description', 'icon']
    pk_url_kwarg = "type_id"

class ProductListView(CanEditPropMixin, ListView):
    """
    A list view for the admins
    """
    model = Product
    template_name = 'counter/product_list.jinja'

class ProductCreateView(CanCreateMixin, CreateView):
    """
    A create view for the admins
    """
    model = Product
    fields = ['name', 'description', 'product_type', 'code', 'purchase_price',
            'selling_price', 'special_selling_price', 'icon', 'club']
    template_name = 'core/create.jinja'

class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'product_type', 'code', 'purchase_price',
                'selling_price', 'special_selling_price', 'icon', 'club', 'limit_age', 'tray']
    counters = make_ajax_field(Product, 'counters', 'counters', show_help_text=False, label='Counters', help_text="Guy",
            required=False) # TODO FIXME

class ProductEditView(CanEditPropMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = Product
    form_class = ProductEditForm
    pk_url_kwarg = "product_id"
    template_name = 'core/edit.jinja'
    # TODO: add management of the 'counters' ForeignKey


class RefillingDeleteView(CanEditPropMixin, DeleteView):
    """
    Delete a refilling (for the admins)
    """
    model = Refilling
    pk_url_kwarg = "refilling_id"
    template_name = 'core/delete_confirm.jinja'

    def get_success_url(self):
        return reverse_lazy('core:user_account', kwargs={'user_id': self.object.customer.user.id})

class SellingDeleteView(CanEditPropMixin, DeleteView):
    """
    Delete a selling (for the admins)
    """
    model = Selling
    pk_url_kwarg = "selling_id"
    template_name = 'core/delete_confirm.jinja'

    def get_success_url(self):
        return reverse_lazy('core:user_account', kwargs={'user_id': self.object.customer.user.id})

