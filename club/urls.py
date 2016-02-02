from django.conf.urls import url, include

from club.views import *

urlpatterns = [
    url(r'^$', ClubListView.as_view(), name='club_list'),
    url(r'^(?P<club_id>[0-9]+)/$', ClubView.as_view(), name='club_view'),
    url(r'^(?P<club_id>[0-9]+)/edit$', ClubEditView.as_view(), name='club_edit'),
    url(r'^(?P<club_id>[0-9]+)/members$', ClubEditMembersView.as_view(), name='club_members'),
    url(r'^(?P<club_id>[0-9]+)/prop$', ClubEditPropView.as_view(), name='club_prop'),
    #url(r'^(?P<club_id>[0-9]+)/tools$', ClubToolsView.as_view(), name='club_tools'),

    ## API
    #url(r'^api/markdown$', render_markdown, name='api_markdown'),
]

