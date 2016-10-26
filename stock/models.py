from django.db import models
from django.counter import Counter

class Stock(models.Model):
	""" The Stock class, this one is used to know how many products are left for a specific counter """
	name = models.CharField(_('name'), max_length=64)
	counter = models.OneToOneField(Counter, verbose_name=_('counter'), related_name='stock')
		
	def __str__(self):
        return self.name

class StockItem(models.Model):
	""" The StockItem class, element of the stock """
	name = models.CharField(_('name'), max_length=64)
	unit_quantity = models.IntegerField(_('unit quantity'), default=0)
	effective_quantity = models.IntegerField(_('effective quantity'), default=0)
	stock_owner = models.ForeignKey(Stock, related_name="stock_owner")

	def __str__(self):
		return self.name

