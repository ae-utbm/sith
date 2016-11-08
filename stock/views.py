from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin


from stock.models import Stock

class StockMain(DetailView):
	"""
		The stock view for the counter owner
	"""
	model = Stock
	template_name = 'stock/stock_main.jinja'
	pk_url_kwarg = "stock_id"

class StockCreateView(CreateView):
	"""
		docstring for StockCreateView
	"""

class StockItemCreateView(CreateView):
	"""
	
	"""