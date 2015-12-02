from django.conf.urls import url, include

from core.views import *

urlpatterns = [
    #url('^', include('django.contrib.auth.urls')),

    url(r'^$', index, name='index'),

    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^password_change/$', password_change, name='password_change'),
    url(r'^password_change/done$', password_change_done, name='password_change_done'),
    url(r'^password_reset/$', password_reset, name='password_reset'),
    url(r'^password_reset/done$', password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', password_reset_complete, name='password_reset_complete'),
    url(r'^register$', register, name='register'),

    url(r'^group/$', GroupListView.as_view(), name='group_list'),
    url(r'^group/(?P<group_id>[0-9]+)/$', GroupEditView.as_view(), name='group_edit'),

    url(r'^user/$', UserListView.as_view(), name='user_list'),
    url(r'^user/(?P<user_id>[0-9]+)/$', UserView.as_view(), name='user_profile'),
    url(r'^user/(?P<user_id>[0-9]+)/edit$', UserUpdateProfileView.as_view(), name='user_edit'),
    url(r'^user/(?P<user_id>[0-9]+)/groups$', UserUpdateGroupsView.as_view(), name='user_groups'),

    url(r'^page/$', PageListView.as_view(), name='page_list'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/edit$', PageEditView.as_view(), name='page_edit'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/prop$', PagePropView.as_view(), name='page_prop'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/hist$', PageHistView.as_view(), name='page_hist'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/rev/(?P<rev>[0-9]+)/', PageRevView.as_view(), name='page_rev'),
    url(r'^page/(?P<page_name>[a-z0-9/]*)/$', PageView.as_view(), name='page'),
]

