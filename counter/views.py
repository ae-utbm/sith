from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from counter.models import Counter

class CounterDetail(CanViewMixin, DetailView):
    """
    The public (barman) view
    """
    model = Counter
    template_name = 'counter/counter_detail.jinja'
    pk_url_kwarg = "counter_id"

class CounterLogin(RedirectView):
    permanent = False
    def post(self): # TODO: finish that
        print(self.request)
        form = AuthenticationForm(self.request, data=self.request.POST)
        if form.is_valid():
            print("Barman logged")

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


