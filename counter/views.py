from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.core.urlresolvers import reverse_lazy

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from counter.models import Counter
# Create your views here.

class CounterListView(CanViewMixin, ListView):
    model = Counter
    template_name = 'counter/counter_list.jinja'

class CounterDetail(CanViewMixin, DetailView):
    model = Counter
    template_name = 'counter/counter_detail.jinja'
    pk_url_kwarg = "counter_id"

class CounterEditView(CanEditMixin, UpdateView):
    """
    Edit a Counter's main informations (for the counter's members)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    pk_url_kwarg = "counter_id"
    template_name = 'counter/counter_edit.jinja'

class CounterCreateView(CanEditMixin, CreateView):
    """
    Edit a Counter's main informations (for the counter's members)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    template_name = 'counter/counter_edit.jinja'

class CounterDeleteView(CanEditMixin, DeleteView):
    """
    Edit a Counter's main informations (for the counter's members)
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('counter:admin_list')
