from django.conf.urls import url, include

from com.views import *

urlpatterns = [
    url(r'^sith/edit/alert$', AlertMsgEditView.as_view(), name='alert_edit'),
    url(r'^sith/edit/info$', InfoMsgEditView.as_view(), name='info_edit'),
    url(r'^sith/edit/index$', IndexEditView.as_view(), name='index_edit'),
    url(r'^weekmail$', WeekmailEditView.as_view(), name='weekmail'),
    url(r'^weekmail/preview$', WeekmailPreviewView.as_view(), name='weekmail_preview'),
    url(r'^weekmail/club/(?P<club_id>[0-9]+)/new_article$', WeekmailArticleCreateView.as_view(), name='weekmail_article'),
    url(r'^weekmail/article/(?P<article_id>[0-9]+)/delete$', WeekmailArticleDeleteView.as_view(), name='weekmail_article_delete'),
    url(r'^weekmail/article/(?P<article_id>[0-9]+)/edit$', WeekmailArticleEditView.as_view(), name='weekmail_article_edit'),
    url(r'^news$', NewsListView.as_view(), name='news_list'),
    url(r'^news/admin$', NewsAdminListView.as_view(), name='news_admin_list'),
    url(r'^news/create$', NewsCreateView.as_view(), name='news_new'),
    url(r'^news/(?P<news_id>[0-9]+)/moderate$', NewsModerateView.as_view(), name='news_moderate'),
    url(r'^news/(?P<news_id>[0-9]+)/edit$', NewsEditView.as_view(), name='news_edit'),
    url(r'^news/(?P<news_id>[0-9]+)$', NewsDetailView.as_view(), name='news_detail'),
]

