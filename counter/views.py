from django.shortcuts import render
from django.views.generic import ListView, DetailView

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
