from django.conf.urls import include, url

from stock.views import *

urlpatterns = [
#Stock urls
    url(r'^new/counter/(?P<counter_id>[0-9]+)$', StockCreateView.as_view(), name='new'),
    url(r'^edit/(?P<stock_id>[0-9]+)$', StockEditView.as_view(), name='edit'),
    url(r'^list$', StockListView.as_view(), name='list'),

# StockItem urls
    url(r'^(?P<stock_id>[0-9]+)$', StockItemList.as_view(), name='items_list'),
    url(r'^(?P<stock_id>[0-9]+)/stockItem/newItem$', StockItemCreateView.as_view(), name='new_item'),
    url(r'^stockItem/(?P<item_id>[0-9]+)/edit$', StockItemEditView.as_view(), name='edit_item'),

# ShoppingList urls
    url(r'^(?P<stock_id>[0-9]+)/shoppingList/list$', StockShoppingListView.as_view(), name='shoppinglist_list'),
    url(r'^(?P<stock_id>[0-9]+)/shoppingList/create$', StockItemQuantityBaseFormView.as_view(), name='shoppinglist_create'),
    url(r'^(?P<stock_id>[0-9]+)/shoppingList/(?P<shoppinglist_id>[0-9]+)/items$', StockShoppingListItemListView.as_view(),
    	name='shoppinglist_items'),
    url(r'^(?P<stock_id>[0-9]+)/shoppingList/(?P<shoppinglist_id>[0-9]+)/delete$', StockShoppingListDeleteView.as_view(),
    	name='shoppinglist_delete'),
	url(r'^(?P<stock_id>[0-9]+)/shoppingList/(?P<shoppinglist_id>[0-9]+)/setDone$', StockShopppingListSetDone.as_view(),
    	name='shoppinglist_set_done'),
	url(r'^(?P<stock_id>[0-9]+)/shoppingList/(?P<shoppinglist_id>[0-9]+)/setTodo$', StockShopppingListSetTodo.as_view(),
    	name='shoppinglist_set_todo'),
    url(r'^(?P<stock_id>[0-9]+)/shoppingList/(?P<shoppinglist_id>[0-9]+)/updateStock$', StockUpdateAfterShopppingBaseFormView.as_view(),
        name='update_after_shopping'),
]
