from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from counter.models import Counter, ProductType

class Stock(models.Model):
	"""
	The Stock class, this one is used to know how many products are left for a specific counter
	"""
	name = models.CharField(_('name'), max_length=64)
	counter = models.OneToOneField(Counter, verbose_name=_('counter'), related_name='stock')

	def __str__(self):
		return "%s (%s)" % (self.name, self.counter)

	def get_absolute_url(self):
		return reverse('stock:list')

class StockItem(models.Model):
	"""
	The StockItem class, element of the stock
	"""
	name = models.CharField(_('name'), max_length=64)
	unit_quantity = models.IntegerField(_('unit quantity'), default=0, help_text='number of element in one box')
	effective_quantity = models.IntegerField(_('effective quantity'), default=0, help_text='number of box')
	type = models.ForeignKey(ProductType, related_name="stock_items", verbose_name=_("type"), null=True, blank=True,
		on_delete=models.SET_NULL)
	stock_owner = models.ForeignKey(Stock, related_name="items")

	def __str__(self):
		return "%s" % (self.name)

	def get_absolute_url(self):
		return reverse('stock:items_list', kwargs={'stock_id':self.stock_owner.id})

class ShoppingList(models.Model):
	"""
	The ShoppingList class, used to make an history of the shopping lists
	"""
	date = models.DateTimeField(_('date'))
	name = models.CharField(_('name'), max_length=64)
	todo = models.BooleanField(_('todo'))
	items_to_buy = models.ManyToManyField(StockItem, verbose_name=_('items to buy'), related_name="shopping_lists")
	stock_owner = models.ForeignKey(Stock, null=True, related_name="shopping_lists")

	def __str__(self):
		return "%s (%s)" % (self.name, self.effective_quantity)

	def get_absolute_url(self):
		return reverse('stock:shoppinglist_list')
