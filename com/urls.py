from django.conf.urls import url, include

from com.views import *

urlpatterns = [
    url(r'^sith/edit/alert$', AlertMsgEditView.as_view(), name='alert_edit'),
    url(r'^sith/edit/info$', InfoMsgEditView.as_view(), name='info_edit'),
    url(r'^sith/edit/index$', IndexEditView.as_view(), name='index_edit'),
    url(r'^news$', NewsListView.as_view(), name='news_list'),
    url(r'^news/admin$', NewsAdminListView.as_view(), name='news_admin_list'),
    url(r'^news/create$', NewsCreateView.as_view(), name='news_new'),
    url(r'^news/(?P<news_id>[0-9]+)/edit$', NewsEditView.as_view(), name='news_edit'),
    url(r'^news/(?P<news_id>[0-9]+)$', NewsDetailView.as_view(), name='news_detail'),
]

