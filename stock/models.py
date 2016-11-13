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
	unit_quantity = models.IntegerField(_('unit quantity'), default=0, help_text='number of beer in one crate (equal one for barrels)')
	effective_quantity = models.IntegerField(_('effective quantity'), default=0, help_text='total number of bottle/barrel')
	type = models.ForeignKey(ProductType, related_name="stockItem_type", verbose_name=_("type"), null=True, blank=True,
		on_delete=models.SET_NULL)
	stock_owner = models.ForeignKey(Stock, related_name="stock_owner")


	def __str__(self):
		return "%s (%s)" % (self.name, self.stock_owner)

