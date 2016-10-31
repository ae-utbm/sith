from django.conf.urls import include, url

from stock.views import *

urlpatterns = [
    url(r'^(?P<counter_id>[0-9]+)$', StockListView.as_view(), name='stock_list'),
    url(r'^(?P<counter_id>[0-9]+)/new$', StockCreateView.as_view(), name='stock_new'),
]
