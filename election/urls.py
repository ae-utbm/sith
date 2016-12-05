from django.conf.urls import url, include

from election.views import *

urlpatterns = [
    url(r'^$', ElectionsListView.as_view(), name='election_list'),
]