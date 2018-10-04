# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Guillaume "Lo-J" Renaud <renaudg779@gmail.com>
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings


from counter.models import Counter, ProductType


class Stock(models.Model):
    """
    The Stock class, this one is used to know how many products are left for a specific counter
    """

    name = models.CharField(_("name"), max_length=64)
    counter = models.OneToOneField(
        Counter, verbose_name=_("counter"), related_name="stock"
    )

    def __str__(self):
        return "%s (%s)" % (self.name, self.counter)

    def get_absolute_url(self):
        return reverse("stock:list")

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)


class StockItem(models.Model):
    """
    The StockItem class, element of the stock
    """

    name = models.CharField(_("name"), max_length=64)
    unit_quantity = models.IntegerField(
        _("unit quantity"), default=0, help_text=_("number of element in one box")
    )
    effective_quantity = models.IntegerField(
        _("effective quantity"), default=0, help_text=_("number of box")
    )
    minimal_quantity = models.IntegerField(
        _("minimal quantity"),
        default=1,
        help_text=_(
            "if the effective quantity is less than the minimal, item is added to the shopping list"
        ),
    )
    type = models.ForeignKey(
        ProductType,
        related_name="stock_items",
        verbose_name=_("type"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    stock_owner = models.ForeignKey(Stock, related_name="items")

    def __str__(self):
        return "%s" % (self.name)

    def get_absolute_url(self):
        return reverse("stock:items_list", kwargs={"stock_id": self.stock_owner.id})

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)


class ShoppingList(models.Model):
    """
    The ShoppingList class, used to make an history of the shopping lists
    """

    date = models.DateTimeField(_("date"))
    name = models.CharField(_("name"), max_length=64)
    todo = models.BooleanField(_("todo"))
    comment = models.TextField(_("comment"), null=True, blank=True)
    stock_owner = models.ForeignKey(Stock, null=True, related_name="shopping_lists")

    def __str__(self):
        return "%s (%s)" % (self.name, self.date)

    def get_absolute_url(self):
        return reverse("stock:shoppinglist_list")

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)


class ShoppingListItem(models.Model):
    """
    """

    shopping_lists = models.ManyToManyField(
        ShoppingList,
        verbose_name=_("shopping lists"),
        related_name="shopping_items_to_buy",
    )
    stockitem_owner = models.ForeignKey(
        StockItem, related_name="shopping_item", null=True
    )
    name = models.CharField(_("name"), max_length=64)
    type = models.ForeignKey(
        ProductType,
        related_name="shoppinglist_items",
        verbose_name=_("type"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tobuy_quantity = models.IntegerField(
        _("quantity to buy"),
        default=6,
        help_text=_("quantity to buy during the next shopping session"),
    )
    bought_quantity = models.IntegerField(
        _("quantity bought"),
        default=0,
        help_text=_("quantity bought during the last shopping session"),
    )

    def __str__(self):
        return "%s - %s" % (self.name, self.shopping_lists.first())

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_COUNTER_ADMIN_ID)

    def get_absolute_url(self):
        return reverse("stock:shoppinglist_list")
