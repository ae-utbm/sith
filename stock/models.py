from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings


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

	def can_be_viewed_by(self, user):
		return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)

class StockItem(models.Model):
	"""
	The StockItem class, element of the stock
	"""
	name = models.CharField(_('name'), max_length=64)
	unit_quantity = models.IntegerField(_('unit quantity'), default=0, help_text='number of element in one box')
	effective_quantity = models.IntegerField(_('effective quantity'), default=0, help_text='number of box')
	minimal_quantity = models.IntegerField(_('minimal quantity'), default=1, 
		help_text='if the effective quantity is less than the minimal, item is added to the shopping list')
	type = models.ForeignKey(ProductType, related_name="stock_items", verbose_name=_("type"), null=True, blank=True,
		on_delete=models.SET_NULL)
	stock_owner = models.ForeignKey(Stock, related_name="items")

	def __str__(self):
		return "%s" % (self.name)

	def get_absolute_url(self):
		return reverse('stock:items_list', kwargs={'stock_id':self.stock_owner.id})

	def can_be_viewed_by(self, user):
		return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)

class ShoppingList(models.Model):
	"""
	The ShoppingList class, used to make an history of the shopping lists
	"""
	date = models.DateTimeField(_('date'))
	name = models.CharField(_('name'), max_length=64)
	todo = models.BooleanField(_('todo'))
	comment = models.TextField(_('comment'), null=True, blank=True)
	stock_owner = models.ForeignKey(Stock, null=True, related_name="shopping_lists")

	def __str__(self):
		return "%s (%s)" % (self.name, self.date)

	def get_absolute_url(self):
		return reverse('stock:shoppinglist_list')

	def can_be_viewed_by(self, user):
		return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)


class ShoppingListItem(models.Model):
	"""
	"""
	shopping_lists = models.ManyToManyField(ShoppingList, verbose_name=_('shopping lists'), related_name="shopping_items_to_buy")
	stockitem_owner = models.ForeignKey(StockItem, related_name="shopping_item", null=True)
	name = models.CharField(_('name'), max_length=64)
	type = models.ForeignKey(ProductType, related_name="shoppinglist_items", verbose_name=_("type"), null=True, blank=True,
		on_delete=models.SET_NULL)
	tobuy_quantity = models.IntegerField(_('quantity to buy'), default=6, help_text="quantity to buy during the next shopping session")
	bought_quantity = models.IntegerField(_('quantity bought'), default=0, help_text="quantity bought during the last shopping session")

	def __str__(self):
		return "%s - %s" % (self.name, self.shopping_lists.first())

	def can_be_viewed_by(self, user):
		return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)

	def get_absolute_url(self):
		return reverse('stock:shoppinglist_list')
		
