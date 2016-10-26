from django.db import models
from django.counter import Counter

class Stock(models.Model):
	""" The Stock class, this one is used to know how many products are left for a specific counter """
	name = models.CharField(_('name'), max_length=64)
	counter = models.OneToOneField(Counter, verbose_name=_('counter'), related_name='stock')
		
	def __str__(self):
        return self.name