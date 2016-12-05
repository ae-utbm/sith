from django.conf.urls import url, include

from election.views import *

urlpatterns = [
    url(r'^$', ElectionsListView.as_view(), name='list'),
    url(r'^/(?P<election_id>[0-9]+)/detail$', ElectionDetailView.as_view(), name='detail'),
]
