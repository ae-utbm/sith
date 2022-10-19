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

from django.urls import include, path

from stock.views import *

urlpatterns = [
    # Stock re_paths
    path("new/counter/<int:counter_id>/", StockCreateView.as_view(), name="new"),
    path("edit/<int:stock_id>/", StockEditView.as_view(), name="edit"),
    path("list/", StockListView.as_view(), name="list"),
    # StockItem re_paths
    path("<int:stock_id>/", StockItemList.as_view(), name="items_list"),
    path(
        "<int:stock_id>/stock_item/new_item/",
        StockItemCreateView.as_view(),
        name="new_item",
    ),
    path(
        "stock_item/(?P<item_id>[0-9]+)/edit/",
        StockItemEditView.as_view(),
        name="edit_item",
    ),
    path(
        "<int:stock_id>/stock_item/take_items/",
        StockTakeItemsBaseFormView.as_view(),
        name="take_items",
    ),
    # ShoppingList re_paths
    path(
        "<int:stock_id>/shopping_list/list/",
        StockShoppingListView.as_view(),
        name="shoppinglist_list",
    ),
    path(
        "<int:stock_id>/shopping_list/create/",
        StockItemQuantityBaseFormView.as_view(),
        name="shoppinglist_create",
    ),
    path(
        "<int:stock_id>/shopping_list/<int:shoppinglist_id>/items/",
        StockShoppingListItemListView.as_view(),
        name="shoppinglist_items",
    ),
    path(
        "<int:stock_id>/shopping_list/<int:shoppinglist_id>/delete/",
        StockShoppingListDeleteView.as_view(),
        name="shoppinglist_delete",
    ),
    path(
        "<int:stock_id>/shopping_list/<int:shoppinglist_id>/set_done/",
        StockShopppingListSetDone.as_view(),
        name="shoppinglist_set_done",
    ),
    path(
        "<int:stock_id>/shopping_list/<int:shoppinglist_id>/set_todo/",
        StockShopppingListSetTodo.as_view(),
        name="shoppinglist_set_todo",
    ),
    path(
        "<int:stock_id>/shopping_list/<int:shoppinglist_id>/update_stock/",
        StockUpdateAfterShopppingBaseFormView.as_view(),
        name="update_after_shopping",
    ),
]
