from django.conf.urls import url, include

from counter.views import *

urlpatterns = [
    url(r'^$', CounterListView.as_view(), name='list'),
    url(r'^(?P<counter_id>[0-9]+)$', CounterDetail.as_view(), name='details'),
]


