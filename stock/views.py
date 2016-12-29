from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.forms.models import modelform_factory
from django.core.urlresolvers import reverse_lazy, reverse

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from counter.views import CounterAdminTabsMixin
from counter.models import Counter
from stock.models import Stock, StockItem



class StockItemList(CounterAdminTabsMixin, CanCreateMixin, ListView):
	"""
	The stockitems list view for the counter owner
	"""
	model = Stock
	template_name = 'stock/stock_item_list.jinja'
	pk_url_kwarg = "stock_id"
	current_tab = "stocks"

class StockListView(CounterAdminTabsMixin, CanViewMixin, ListView):
	"""
	A list view for the admins
	"""
	model = Stock
	template_name = 'stock/stock_list.jinja'
	current_tab = "stocks"


class StockEditForm(forms.ModelForm):
	"""
	A form to change stock's characteristics
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
	An edit view for the stock
	"""
	model = Stock
	form_class = StockEditForm
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
	A form to change stock's characteristics
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
	An edit view for the stock
	"""
	model = Stock
	form_class = StockEditForm
	pk_url_kwarg = "stock_id"
	template_name = 'core/edit.jinja'
	current_tab = "stocks"


class StockItemEditView(CounterAdminTabsMixin, CanEditPropMixin, UpdateView):
	"""
	An edit view for a stock item
	"""
	model = StockItem
	form_class = modelform_factory(StockItem, fields=['name', 'unit_quantity', 'effective_quantity', 'type', 'stock_owner'])
	pk_url_kwarg = "item_id"
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
		if 'counter_id' in self.kwargs.keys():
			ret['counter'] = self.kwargs['counter_id']
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
		if 'stock_id' in self.kwargs.keys():
			ret['stock_owner'] = self.kwargs['stock_id']
		return ret

	def get_success_url(self):
		return reverse_lazy('stock:items_list', kwargs={'stock_id':self.object.stock_owner.id})


class StockShoppingListView(CounterAdminTabsMixin, CanViewMixin, ListView):
	"""
	A list view for the people to know the item to buy
	"""
	model = Stock
	template_name = "stock/stock_shopping_list.jinja"
	pk_url_kwarg = "stock_id"
	current_tab = "stocks"

	def get_context_data(self):
		ret = super(StockShoppingListView, self).get_context_data()
		if 'stock_id' in self.kwargs.keys():
			ret['stock'] = Stock.objects.filter(id=self.kwargs['stock_id']).first();
		return ret


class StockItemQuantityForm(forms.BaseForm):
	def clean(self):
		with transaction.atomic():
			self.stock = Stock.objects.filter(id=self.stock_id).first()
			shopping_list = ShoppingList(name="Courses "+self.stock.counter.name, date=timezone.now(), todo=True)
			shopping_list.save()
			shopping_list.stock_owner = self.stock
			shopping_list.save()
			for k,t in self.cleaned_data.items():
				if int(t) > 0 :
					item_id = int(k[5:])
					item = StockItem.objects.filter(id=item_id).first()
					item.tobuy_quantity = t
					item.shopping_lists.add(shopping_list)
					item.save()

		return self.cleaned_data

class StockItemQuantityBaseFormView(CounterAdminTabsMixin, CanEditMixin, DetailView, BaseFormView):
	"""
	docstring for StockItemOutList
	"""
	model = StockItem
	template_name = "stock/shopping_list_quantity.jinja"
	pk_url_kwarg = "stock_id"
	current_tab = "stocks"

	def get_form_class(self):
		fields = OrderedDict()
		kwargs = {}
		for t in ProductType.objects.order_by('name').all():
			for i in self.stock.items.filter(type=t).order_by('name').all():
				if i.effective_quantity <= i.minimal_quantity:	            
					field_name = "item-%s" % (str(i.id))
					fields[field_name] = forms.CharField(max_length=30, required=True, label=str(i),
								help_text=str(i.effective_quantity)+" left")
					kwargs[field_name] = i.effective_quantity
		kwargs['stock_id'] = self.stock.id
		kwargs['base_fields'] = fields
		return type('StockItemQuantityForm', (StockItemQuantityForm,), kwargs)

	def get(self, request, *args, **kwargs):
		"""
		Simple get view
		"""
		self.stock = Stock.objects.filter(id=self.kwargs['stock_id']).first()
		return super(StockItemQuantityBaseFormView, self).get(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		"""
		Handle the many possibilities of the post request
		"""
		self.object = self.get_object()
		self.stock = Stock.objects.filter(id=self.kwargs['stock_id']).first()
		return super(StockItemQuantityBaseFormView, self).post(request, *args, **kwargs)

	def form_valid(self, form):
		"""
		We handle here the redirection, passing the user id of the asked customer
		"""
		return super(StockItemQuantityBaseFormView, self).form_valid(form)

	def get_context_data(self, **kwargs):
		"""
    	We handle here the login form for the barman
    	"""
		kwargs = super(StockItemQuantityBaseFormView, self).get_context_data(**kwargs)
		if 'form' not in kwargs.keys():
			kwargs['form'] = self.get_form()
		kwargs['stock'] = self.stock
		return kwargs

	def get_success_url(self):
		return reverse_lazy('stock:shoppinglist_list', args=self.args, kwargs=self.kwargs)


class StockShoppingListItemListView(CounterAdminTabsMixin, CanViewMixin, ListView):
	"""docstring for StockShoppingListItemListView"""
	model = ShoppingList
	template_name = "stock/shopping_list_items.jinja"
	pk_url_kwarg = "shoppinglist_id"
	current_tab = "stocks"

	def get_context_data(self):
		ret = super(StockShoppingListItemListView, self).get_context_data()
		if 'shoppinglist_id' in self.kwargs.keys():
			ret['shoppinglist'] = ShoppingList.objects.filter(id=self.kwargs['shoppinglist_id']).first();
		return ret

class StockShoppingListDeleteView(CounterAdminTabsMixin, CanEditMixin, DeleteView):
    """
    Delete a ShoppingList (for the resonsible account)
    """
    model = ShoppingList
    pk_url_kwarg = "shoppinglist_id"
    template_name = 'core/delete_confirm.jinja'
    current_tab = "stocks"

    def get_success_url(self):
    	return reverse_lazy('stock:shoppinglist_list', kwargs={'stock_id':self.object.stock_owner.id})


class StockShopppingListSetDone(CanEditMixin, DetailView):
    """
    Set a ShoppingList as done
    """
    model = ShoppingList
    pk_url_kwarg = "shoppinglist_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.todo = False
        self.object.save()
        return HttpResponseRedirect(reverse('stock:shoppinglist_list', args=self.args, kwargs={'stock_id':self.object.stock_owner.id}))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(reverse('stock:shoppinglist_list', args=self.args, kwargs={'stock_id':self.object.stock_owner.id}))


class StockShopppingListSetTodo(CanEditMixin, DetailView):
    """
    Set a ShoppingList as done
    """
    model = ShoppingList
    pk_url_kwarg = "shoppinglist_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.todo = True
        self.object.save()
        return HttpResponseRedirect(reverse('stock:shoppinglist_list', args=self.args, kwargs={'stock_id':self.object.stock_owner.id}))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(reverse('stock:shoppinglist_list', args=self.args, kwargs={'stock_id':self.object.stock_owner.id}))
