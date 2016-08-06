from django.conf.urls import url, include

from launderette.views import *

urlpatterns = [
    # views
    url(r'^$', LaunderetteMainView.as_view(), name='launderette_main'),
    url(r'^book$', LaunderetteBookMainView.as_view(), name='book_main'),
    url(r'^book/(?P<launderette_id>[0-9]+)$', LaunderetteBookView.as_view(), name='book_slot'),
    url(r'^(?P<launderette_id>[0-9]+)/click$', LaunderetteMainClickView.as_view(), name='main_click'),
    url(r'^(?P<launderette_id>[0-9]+)/click/(?P<user_id>[0-9]+)$', LaunderetteClickView.as_view(), name='click'),
    url(r'^admin$', LaunderetteListView.as_view(), name='launderette_list'),
    url(r'^admin/(?P<launderette_id>[0-9]+)$', LaunderetteAdminView.as_view(), name='launderette_admin'),
    url(r'^admin/(?P<launderette_id>[0-9]+)/edit$', LaunderetteEditView.as_view(), name='launderette_edit'),
    url(r'^admin/new$', LaunderetteCreateView.as_view(), name='launderette_new'),
    url(r'^admin/machine/new$', MachineCreateView.as_view(), name='machine_new'),
    url(r'^admin/machine/(?P<machine_id>[0-9]+)/edit$', MachineEditView.as_view(), name='machine_edit'),
    url(r'^admin/machine/(?P<machine_id>[0-9]+)/delete$', MachineDeleteView.as_view(), name='machine_delete'),
]



