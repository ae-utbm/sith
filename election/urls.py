from django.conf.urls import url

from election.views import *

urlpatterns = [
    url(r'^$', ElectionsListView.as_view(), name='list'),
    url(r'^add$', ElectionCreateView.as_view(), name='create'),
    url(r'^(?P<election_id>[0-9]+)/edit$', ElectionUpdateView.as_view(), name='update'),
    url(r'^(?P<election_id>[0-9]+)/list/add$', ElectionListCreateView.as_view(), name='create_list'),
    url(r'^(?P<election_id>[0-9]+)/role/create$', RoleCreateView.as_view(), name='create_role'),
    url(r'^(?P<election_id>[0-9]+)/candidate/add$', CandidatureCreateView.as_view(), name='candidate'),
    url(r'^(?P<election_id>[0-9]+)/vote$', VoteFormView.as_view(), name='vote'),
    url(r'^(?P<election_id>[0-9]+)/detail$', ElectionDetailView.as_view(), name='detail'),
]
