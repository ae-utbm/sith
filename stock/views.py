from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.models import modelform_factory
from django.core.urlresolvers import reverse_lazy, reverse

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from counter.views import CounterAdminTabsMixin
from counter.models import Counter
from stock.models import Stock, StockItem



class StockMain(CounterAdminTabsMixin, CanCreateMixin, DetailView):
	"""
	The stock view for the counter owner
	"""
	model = StockItem
	template_name = 'stock/stock_item_list.jinja'
	pk_url_kwarg = "stock_id"
	current_tab = "stocks"

	def get_context_data(self, **kwargs):
		context = super(StockItemList, self).get_context_data(**kwargs)
		if 'stock' in self.request.GET.keys():
			context['stock'] = Stock.objects.filter(id=self.request.GET['stock']).first()
		return context

class StockListView(CounterAdminTabsMixin, CanViewMixin, ListView):
	"""
	A list view for the admins
	"""
	model = Stock
	template_name = 'stock/stock_list.jinja'
	current_tab = "stocks"


class StockEditForm(forms.ModelForm):
	"""
	docstring for StockEditForm"forms.ModelForm
	"""
	class Meta:
		model = Stock
		fields = ['name', 'counter']
			
	def __init__(self, *args, **kwargs):
		super(StockEditForm, self).__init__(*args, **kwargs)

	def save(self, *args, **kwargs):
		return super(StockEditForm, self).save(*args, **kwargs)
		

class StockEditView(CounterAdminTabsMixin, CanEditPropMixin, UpdateView):
	"""
	A edit view for the stock
	"""
	model = Stock
	form_class = StockEditForm
	pk_url_kwarg = "stock_id"
	template_name = 'core/edit.jinja'
	current_tab = "stocks"


class StockCreateView(CounterAdminTabsMixin, CanCreateMixin, CreateView):
	"""
	A create view for a new Stock
	"""
	model = Stock
	form_class = modelform_factory(Stock, fields=['name', 'counter'])
	template_name = 'core/create.jinja'
	pk_url_kwarg = "counter_id"
	current_tab = "stocks"
	success_url = reverse_lazy('stock:list')

	def get_initial(self):
		ret = super(StockCreateView, self).get_initial()
		if 'counter' in self.request.GET.keys():
			ret['counter'] = self.request.GET['counter']
		return ret
		
class StockItemCreateView(CounterAdminTabsMixin, CanCreateMixin, CreateView):
	"""
	A create view for a new StockItem
	"""
			
	model = StockItem
	form_class = modelform_factory(StockItem, fields=['name', 'unit_quantity', 'effective_quantity', 'type', 'stock_owner'])
	template_name = 'core/create.jinja'
	pk_url_kwarg = "stock_id"
	current_tab = "stocks"

	def get_initial(self):
		ret = super(StockItemCreateView, self).get_initial()
		if 'stock' in self.request.GET.keys():
			ret['stock_owner'] = self.request.GET['stock']
		return ret

	def get_success_url(self):
		return reverse_lazy('stock:main', kwargs={'stock_id': self.object.stock_owner.id})
