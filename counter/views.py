from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils import timezone
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import DataError, transaction

import re
import pytz
from datetime import date, timedelta, datetime
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField
from ajax_select import make_ajax_form, make_ajax_field

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from core.views.forms import SelectUser, LoginForm
from core.models import User
from subscription.models import Subscriber, Subscription
from subscription.views import get_subscriber
from counter.models import Counter, Customer, Product, Selling, Refilling, ProductType, CashRegisterSummary, CashRegisterSummaryItem
from accounting.models import CurrencyField

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
            cus = Customer.objects.filter(account_id__iexact=cleaned_data['code']).first()
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
        self.object.update_activity()
        kwargs = super(CounterMain, self).get_context_data(**kwargs)
        kwargs['login_form'] = LoginForm()
        kwargs['login_form'].fields['username'].widget.attrs['autofocus'] = True
        kwargs['login_form'].cleaned_data = {} # add_error fails if there are no cleaned_data
        if "credentials" in self.request.GET:
            kwargs['login_form'].add_error(None, _("Bad credentials"))
        if "sellers" in self.request.GET:
            kwargs['login_form'].add_error(None, _("User is not barman"))
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
        request.session['not_enough'] = False # Reset every variable
        request.session['too_young'] = False
        request.session['not_allowed'] = False
        request.session['no_age'] = False
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
        request.session['not_enough'] = False # Reset every variable
        request.session['too_young'] = False
        request.session['not_allowed'] = False
        request.session['no_age'] = False
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

    def get_total_quantity_for_pid(self, request, pid):
        pid = str(pid)
        try:
            return request.session['basket'][pid]['qty'] + request.session['basket'][pid]['bonus_qty']
        except:
            return 0

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
        product = self.get_product(pid)
        can_buy = False
        if not product.buying_groups.exists():
            can_buy = True
        else:
            for g in product.buying_groups.all():
                if self.customer.user.is_in_group(g.name):
                    can_buy = True
        if not can_buy:
            request.session['not_allowed'] = True
            return False
        bq = 0 # Bonus quantity, for trays
        if product.tray: # Handle the tray to adjust the quantity q to add and the bonus quantity bq
            total_qty_mod_6 = self.get_total_quantity_for_pid(request, pid) % 6
            bq = int((total_qty_mod_6 + q) / 6) # Integer division
            q -= bq
        if self.customer.amount < (total + q*float(price)): # Check for enough money
            request.session['not_enough'] = True
            return False
        if product.limit_age >= 18 and not self.customer.user.date_of_birth:
            request.session['no_age'] = True
            return False
        if self.customer.user.date_of_birth and self.customer.user.get_age() < product.limit_age: # Check if affordable
            request.session['too_young'] = True
            return False
        if pid in request.session['basket']: # Add if already in basket
            request.session['basket'][pid]['qty'] += q
            request.session['basket'][pid]['bonus_qty'] += bq
        else: # or create if not
            request.session['basket'][pid] = {'qty': q, 'price': int(price*100), 'bonus_qty': bq}
        request.session.modified = True
        return True

    def del_product(self, request):
        """ Delete a product from the basket """
        pid = str(request.POST['product_id'])
        product = self.get_product(pid)
        if pid in request.session['basket']:
            if product.tray and (self.get_total_quantity_for_pid(request, pid) % 6 == 0) and request.session['basket'][pid]['bonus_qty']:
                request.session['basket'][pid]['bonus_qty'] -= 1
            else:
                request.session['basket'][pid]['qty'] -= 1
            if request.session['basket'][pid]['qty'] <= 0:
                del request.session['basket'][pid]
        else:
            request.session['basket'][pid] = None
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
                request.session['last_basket'].append("%d x %s" % (infos['qty']+infos['bonus_qty'], p.name))
                s = Selling(label=p.name, product=p, club=p.club, counter=self.object, unit_price=uprice,
                       quantity=infos['qty'], seller=self.operator, customer=self.customer)
                s.save()
                if infos['bonus_qty']:
                    s = Selling(label=p.name + " (Plateau)", product=p, club=p.club, counter=self.object, unit_price=0,
                           quantity=infos['bonus_qty'], seller=self.operator, customer=self.customer)
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
        kwargs['categories'] = ProductType.objects.all()
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
        self.counter = Counter.objects.filter(id=kwargs['counter_id']).first()
        form = LoginForm(request, data=request.POST)
        self.errors = []
        if form.is_valid():
            user = User.objects.filter(username=form.cleaned_data['username']).first()
            if user in self.counter.sellers.all() and not user in self.counter.get_barmen_list():
                self.counter.add_barman(user)
            else:
                self.errors += ["sellers"]
        else:
            self.errors += ["credentials"]
        return super(CounterLogin, self).post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('counter:details', args=args, kwargs=kwargs)+"?"+'&'.join(self.errors)

class CounterLogout(RedirectView):
    permanent = False
    def post(self, request, *args, **kwargs):
        """
        Unregister the user from the barman
        """
        self.counter = Counter.objects.filter(id=kwargs['counter_id']).first()
        user = User.objects.filter(id=request.POST['user_id']).first()
        self.counter.del_barman(user)
        return super(CounterLogout, self).post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('counter:details', args=args, kwargs=kwargs)

## Counter admin views

class CounterTabsMixin(TabedViewMixin):
    tabs_title = _("Counter administration")
    list_of_tabs = [
            {
                'url': reverse_lazy('counter:admin_list'),
                'slug': 'counters',
                'name': _("Counters"),
                },
            {
                'url': reverse_lazy('counter:product_list'),
                'slug': 'products',
                'name': _("Products"),
                },
            {
                'url': reverse_lazy('counter:product_list_archived'),
                'slug': 'archive',
                'name': _("Archived products"),
                },
            {
                'url': reverse_lazy('counter:producttype_list'),
                'slug': 'product_types',
                'name': _("Product types"),
                },
            {
                'url': reverse_lazy('counter:cash_summary_list'),
                'slug': 'cash_summary',
                'name': _("Cash register summaries"),
                },
            ]

class CounterListView(CounterTabsMixin, CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = Counter
    template_name = 'counter/counter_list.jinja'
    current_tab = "counters"

class CounterEditForm(forms.ModelForm):
    class Meta:
        model = Counter
        fields = ['sellers', 'products']
    sellers = make_ajax_field(Counter, 'sellers', 'users', help_text="")
    products = make_ajax_field(Counter, 'products', 'products', help_text="")

class CounterEditView(CounterTabsMixin, CanEditMixin, UpdateView):
    """
    Edit a counter's main informations (for the counter's manager)
    """
    model = Counter
    form_class = CounterEditForm
    pk_url_kwarg = "counter_id"
    template_name = 'core/edit.jinja'
    current_tab = "counters"

    def get_success_url(self):
        return reverse_lazy('counter:admin', kwargs={'counter_id': self.object.id})

class CounterEditPropView(CounterTabsMixin, CanEditPropMixin, UpdateView):
    """
    Edit a counter's main informations (for the counter's admin)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type'])
    pk_url_kwarg = "counter_id"
    template_name = 'core/edit.jinja'
    current_tab = "counters"

class CounterCreateView(CounterTabsMixin, CanEditMixin, CreateView):
    """
    Create a counter (for the admins)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    template_name = 'core/create.jinja'
    current_tab = "counters"

class CounterDeleteView(CounterTabsMixin, CanEditMixin, DeleteView):
    """
    Delete a counter (for the admins)
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('counter:admin_list')
    current_tab = "counters"

# Product management

class ProductTypeListView(CounterTabsMixin, CanEditPropMixin, ListView):
    """
    A list view for the admins
    """
    model = ProductType
    template_name = 'counter/producttype_list.jinja'
    current_tab = "product_types"

class ProductTypeCreateView(CounterTabsMixin, CanCreateMixin, CreateView):
    """
    A create view for the admins
    """
    model = ProductType
    fields = ['name', 'description', 'icon']
    template_name = 'core/create.jinja'
    current_tab = "products"

class ProductTypeEditView(CounterTabsMixin, CanEditPropMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = ProductType
    template_name = 'core/edit.jinja'
    fields = ['name', 'description', 'icon']
    pk_url_kwarg = "type_id"
    current_tab = "products"

class ProductArchivedListView(CounterTabsMixin, CanEditPropMixin, ListView):
    """
    A list view for the admins
    """
    model = Product
    template_name = 'counter/product_list.jinja'
    queryset = Product.objects.filter(archived=True)
    ordering = ['name']
    current_tab = "archive"

class ProductListView(CounterTabsMixin, CanEditPropMixin, ListView):
    """
    A list view for the admins
    """
    model = Product
    template_name = 'counter/product_list.jinja'
    queryset = Product.objects.filter(archived=False)
    ordering = ['name']
    current_tab = "products"

class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'product_type', 'code', 'parent_product', 'buying_groups', 'purchase_price',
                'selling_price', 'special_selling_price', 'icon', 'club', 'limit_age', 'tray', 'archived']
    parent_product = AutoCompleteSelectField('products', show_help_text=False, label=_("Parent product"), required=False)
    buying_groups = AutoCompleteSelectMultipleField('groups', show_help_text=False, help_text="", label=_("Buying groups"), required=False)
    club = AutoCompleteSelectField('clubs', show_help_text=False)
    counters = AutoCompleteSelectMultipleField('counters', show_help_text=False, help_text="", label=_("Counters"), required=False)

    def __init__(self, *args, **kwargs):
        super(ProductEditForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['counters'].initial = [str(c.id) for c in self.instance.counters.all()]

    def save(self, *args, **kwargs):
        ret = super(ProductEditForm, self).save(*args, **kwargs)
        if self.fields['counters'].initial:
            for cid in self.fields['counters'].initial:
                c = Counter.objects.filter(id=int(cid)).first()
                c.products.remove(self.instance)
                c.save()
        for cid in self.cleaned_data['counters']:
            c = Counter.objects.filter(id=int(cid)).first()
            c.products.add(self.instance)
            c.save()
        return ret

class ProductCreateView(CounterTabsMixin, CanCreateMixin, CreateView):
    """
    A create view for the admins
    """
    model = Product
    form_class = ProductEditForm
    template_name = 'core/create.jinja'
    current_tab = "products"

class ProductEditView(CounterTabsMixin, CanEditPropMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = Product
    form_class = ProductEditForm
    pk_url_kwarg = "product_id"
    template_name = 'core/edit.jinja'
    current_tab = "products"

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

# Cash register summaries

class CashRegisterSummaryForm(forms.Form):
    """
    Provide the cash summary form
    """
    ten_cents = forms.IntegerField(label=_("10 cents"), required=False)
    twenty_cents = forms.IntegerField(label=_("20 cents"), required=False)
    fifty_cents = forms.IntegerField(label=_("50 cents"), required=False)
    one_euro = forms.IntegerField(label=_("1 euro"), required=False)
    two_euros = forms.IntegerField(label=_("2 euros"), required=False)
    five_euros = forms.IntegerField(label=_("5 euros"), required=False)
    ten_euros = forms.IntegerField(label=_("10 euros"), required=False)
    twenty_euros = forms.IntegerField(label=_("20 euros"), required=False)
    fifty_euros = forms.IntegerField(label=_("50 euros"), required=False)
    hundred_euros = forms.IntegerField(label=_("100 euros"), required=False)
    check_1_value = forms.DecimalField(label=_("Check amount"), required=False)
    check_1_quantity = forms.IntegerField(label=_("Check quantity"), required=False)
    check_2_value = forms.DecimalField(label=_("Check amount"), required=False)
    check_2_quantity = forms.IntegerField(label=_("Check quantity"), required=False)
    check_3_value = forms.DecimalField(label=_("Check amount"), required=False)
    check_3_quantity = forms.IntegerField(label=_("Check quantity"), required=False)
    check_4_value = forms.DecimalField(label=_("Check amount"), required=False)
    check_4_quantity = forms.IntegerField(label=_("Check quantity"), required=False)
    check_5_value = forms.DecimalField(label=_("Check amount"), required=False)
    check_5_quantity = forms.IntegerField(label=_("Check quantity"), required=False)
    comment = forms.CharField(label=_("Comment"), required=False)
    emptied = forms.BooleanField(label=_("Emptied"), required=False)

    def save(self, counter):
        cd = self.cleaned_data
        summary = CashRegisterSummary(
                counter=counter,
                user=counter.get_random_barman(),
                comment=cd['comment'],
                emptied=cd['emptied'],
                )
        summary.save()
        # Cash
        if cd['ten_cents']: CashRegisterSummaryItem(cash_summary=summary, value=0.1, quantity=cd['ten_cents']).save()
        if cd['twenty_cents']: CashRegisterSummaryItem(cash_summary=summary, value=0.2, quantity=cd['twenty_cents']).save()
        if cd['fifty_cents']: CashRegisterSummaryItem(cash_summary=summary, value=0.5, quantity=cd['fifty_cents']).save()
        if cd['one_euro']: CashRegisterSummaryItem(cash_summary=summary, value=1, quantity=cd['one_euro']).save()
        if cd['two_euros']: CashRegisterSummaryItem(cash_summary=summary, value=2, quantity=cd['two_euros']).save()
        if cd['five_euros']: CashRegisterSummaryItem(cash_summary=summary, value=5, quantity=cd['five_euros']).save()
        if cd['ten_euros']: CashRegisterSummaryItem(cash_summary=summary, value=10, quantity=cd['ten_euros']).save()
        if cd['twenty_euros']: CashRegisterSummaryItem(cash_summary=summary, value=20, quantity=cd['twenty_euros']).save()
        if cd['fifty_euros']: CashRegisterSummaryItem(cash_summary=summary, value=50, quantity=cd['fifty_euros']).save()
        if cd['hundred_euros']: CashRegisterSummaryItem(cash_summary=summary, value=100, quantity=cd['hundred_euros']).save()
        # Checks
        if cd['check_1_quantity']: CashRegisterSummaryItem(cash_summary=summary, value=cd['check_1_value'], quantity=cd['check_1_quantity']).save()
        if cd['check_2_quantity']: CashRegisterSummaryItem(cash_summary=summary, value=cd['check_2_value'], quantity=cd['check_2_quantity']).save()
        if cd['check_3_quantity']: CashRegisterSummaryItem(cash_summary=summary, value=cd['check_3_value'], quantity=cd['check_3_quantity']).save()
        if cd['check_4_quantity']: CashRegisterSummaryItem(cash_summary=summary, value=cd['check_4_value'], quantity=cd['check_4_quantity']).save()
        if cd['check_5_quantity']: CashRegisterSummaryItem(cash_summary=summary, value=cd['check_5_value'], quantity=cd['check_5_quantity']).save()
        if summary.items.count() < 1:
            summary.delete()

class CounterCashSummaryView(CanViewMixin, DetailView):
    """
    Provide the cash summary form
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'counter/cash_register_summary.jinja'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if len(self.object.get_barmen_list()) < 1:
            return HttpResponseRedirect(reverse_lazy('counter:details', args=self.args,
                kwargs={'counter_id': self.object.id}))
        self.form = CashRegisterSummaryForm()
        return super(CounterCashSummaryView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if len(self.object.get_barmen_list()) < 1:
            return HttpResponseRedirect(reverse_lazy('counter:details', args=self.args,
                kwargs={'counter_id': self.object.id}))
        self.form = CashRegisterSummaryForm(request.POST)
        if self.form.is_valid():
            self.form.save(self.object)
            return HttpResponseRedirect(self.get_success_url())
        return super(CounterCashSummaryView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('counter:details', kwargs={'counter_id': self.object.id})

    def get_context_data(self, **kwargs):
        """ Add form to the context """
        kwargs = super(CounterCashSummaryView, self).get_context_data(**kwargs)
        kwargs['form'] = self.form
        return kwargs

class CounterActivityView(DetailView):
    """
    Show the bar activity
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'counter/activity.jinja'

class CounterStatView(DetailView):
    """
    Show the bar stats
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'counter/stats.jinja'

    def get_context_data(self, **kwargs):
        """ Add stats to the context """
        from django.db.models import Sum, Case, When, F, DecimalField
        kwargs = super(CounterStatView, self).get_context_data(**kwargs)
        kwargs['Customer'] = Customer
        semester_start = Subscription.compute_start(d=date.today(), duration=3)
        kwargs['total_sellings'] = Selling.objects.filter(date__gte=semester_start,
                counter=self.object).aggregate(total_sellings=Sum(F('quantity')*F('unit_price'),
                    output_field=CurrencyField()))['total_sellings']
        kwargs['top'] = Selling.objects.values('customer__user').annotate(
                selling_sum=Sum(
                    Case(When(counter=self.object,
                            date__gte=semester_start,
                            unit_price__gt=0,
                        then=F('unit_price')*F('quantity')),
                        output_field=CurrencyField()
                        )
                    )
                ).exclude(selling_sum=None).order_by('-selling_sum').all()[:100]
        return kwargs


class CashSummaryListView(CanEditPropMixin, CounterTabsMixin, ListView):
    """Display a list of cash summaries"""
    model = CashRegisterSummary
    template_name = 'counter/cash_summary_list.jinja'
    context_object_name = "cashsummary_list"
    current_tab = "cash_summary"

    def get_context_data(self, **kwargs):
        """ Add sums to the context """
        kwargs = super(CashSummaryListView, self).get_context_data(**kwargs)
        kwargs['summaries_sums'] = {}
        kwargs['refilling_sums'] = {}
        for c in Counter.objects.filter(type="BAR").all():
            last_summary = CashRegisterSummary.objects.filter(counter=c, emptied=True).order_by('-date').first()
            if last_summary:
                last_date = last_summary.date
            else:
                last_date = datetime(year=1994, month=5, day=17, tzinfo=pytz.UTC) # My birth date should be old enough
            kwargs['summaries_sums'][c.name] = sum([s.get_total() for s in CashRegisterSummary.objects.filter(counter=c, date__gt=last_date).all()])
            kwargs['refilling_sums'][c.name] = sum([s.amount for s in Refilling.objects.filter(counter=c, date__gt=last_date).all()])
        return kwargs
