from django.conf.urls import url

from election.views import *

urlpatterns = [
    url(r'^$', ElectionsListView.as_view(), name='list'),
    url(r'^create$', ElectionCreateView.as_view(), name='create'),
    url(r'^list/create$', ElectionListCreateView.as_view(), name='create_list'),
    url(r'^role/create$', RoleCreateView.as_view(), name='create_role'),
    url(r'^(?P<election_id>[0-9]+)/candidate$', CandidatureCreateView.as_view(), name='candidate'),
    url(r'^(?P<election_id>[0-9]+)/detail$', ElectionDetailView.as_view(), name='detail'),
]
