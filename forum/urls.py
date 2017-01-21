from django.conf.urls import url, include

from forum.views import *

urlpatterns = [
    url(r'^$', ForumMainView.as_view(), name='main'),
    url(r'^new_forum$', ForumCreateView.as_view(), name='new_forum'),
    url(r'^(?P<forum_id>[0-9]+)$', ForumDetailView.as_view(), name='view_forum'),
    url(r'^(?P<forum_id>[0-9]+)/edit$', ForumEditView.as_view(), name='edit_forum'),
    url(r'^(?P<forum_id>[0-9]+)/new_topic$', ForumTopicCreateView.as_view(), name='new_topic'),
    url(r'^topic/(?P<topic_id>[0-9]+)$', ForumTopicDetailView.as_view(), name='view_topic'),
    url(r'^topic/(?P<topic_id>[0-9]+)/edit$', ForumTopicEditView.as_view(), name='edit_topic'),
    url(r'^topic/(?P<topic_id>[0-9]+)/new_message$', ForumMessageCreateView.as_view(), name='new_message'),
    # url(r'^(?P<club_id>[0-9]+)/tools$', ClubToolsView.as_view(), name='tools'),
]

