from django.conf.urls import url

from core.views import *

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^login$', login, name='login'),
    url(r'^logout$', logout, name='logout'),
    url(r'^register$', register, name='register'),
    url(r'^user/$', user, name='user_list'),
    url(r'^user/(?P<user_id>[0-9]+)/$', user, name='user_profile'),
    url(r'^user/(?P<user_id>[0-9]+)/edit$', user_edit, name='user_edit'),
    url(r'^page/$', PageListView.as_view(), name='page_list'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/$', PageView.as_view(), name='page'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/edit$', PageEditView.as_view(), name='page_edit'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/prop$', PagePropView.as_view(), name='page_prop'),
]

