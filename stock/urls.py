# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from django.urls import path

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
        "stock_item/<int:item_id>/edit/",
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
