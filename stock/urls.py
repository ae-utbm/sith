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

from django.urls import include, re_path

from stock.views import *

urlpatterns = [
    # Stock re_paths
    re_path(
        r"^new/counter/(?P<counter_id>[0-9]+)$", StockCreateView.as_view(), name="new"
    ),
    re_path(r"^edit/(?P<stock_id>[0-9]+)$", StockEditView.as_view(), name="edit"),
    re_path(r"^list$", StockListView.as_view(), name="list"),
    # StockItem re_paths
    re_path(r"^(?P<stock_id>[0-9]+)$", StockItemList.as_view(), name="items_list"),
    re_path(
        r"^(?P<stock_id>[0-9]+)/stock_item/new_item$",
        StockItemCreateView.as_view(),
        name="new_item",
    ),
    re_path(
        r"^stock_item/(?P<item_id>[0-9]+)/edit$",
        StockItemEditView.as_view(),
        name="edit_item",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/stock_item/take_items$",
        StockTakeItemsBaseFormView.as_view(),
        name="take_items",
    ),
    # ShoppingList re_paths
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/list$",
        StockShoppingListView.as_view(),
        name="shoppinglist_list",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/create$",
        StockItemQuantityBaseFormView.as_view(),
        name="shoppinglist_create",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/(?P<shoppinglist_id>[0-9]+)/items$",
        StockShoppingListItemListView.as_view(),
        name="shoppinglist_items",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/(?P<shoppinglist_id>[0-9]+)/delete$",
        StockShoppingListDeleteView.as_view(),
        name="shoppinglist_delete",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/(?P<shoppinglist_id>[0-9]+)/set_done$",
        StockShopppingListSetDone.as_view(),
        name="shoppinglist_set_done",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/(?P<shoppinglist_id>[0-9]+)/set_todo$",
        StockShopppingListSetTodo.as_view(),
        name="shoppinglist_set_todo",
    ),
    re_path(
        r"^(?P<stock_id>[0-9]+)/shopping_list/(?P<shoppinglist_id>[0-9]+)/update_stock$",
        StockUpdateAfterShopppingBaseFormView.as_view(),
        name="update_after_shopping",
    ),
]
