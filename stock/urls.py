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
]
