from django.conf.urls import include, url

from stock.views import *

urlpatterns = [
    url(r'^(?P<stock_id>[0-9]+)$', StockMain.as_view(), name='main'),
    url(r'^new/counter/(?P<counter_id>[0-9]+)$', StockCreateView.as_view(), name='new'),
    url(r'^edit/(?P<stock_id>[0-9]+)$', StockEditView.as_view(), name='edit'),
    url(r'^list$', StockListView.as_view(), name='list'),
    url(r'^(?P<stock_id>[0-9]+)/newItem$', StockItemCreateView.as_view(), name='new_item'),
]
