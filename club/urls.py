from django.conf.urls import url, include

from club.views import *

urlpatterns = [
    url(r'^$', ClubListView.as_view(), name='club_list'),
    url(r'^new$', ClubCreateView.as_view(), name='club_new'),
    url(r'^stats$', ClubStatView.as_view(), name='club_stats'),
    url(r'^(?P<club_id>[0-9]+)/$', ClubView.as_view(), name='club_view'),
    url(r'^(?P<club_id>[0-9]+)/edit$', ClubEditView.as_view(), name='club_edit'),
    url(r'^(?P<club_id>[0-9]+)/members$', ClubMembersView.as_view(), name='club_members'),
    url(r'^(?P<club_id>[0-9]+)/elderlies$', ClubOldMembersView.as_view(), name='club_old_members'),
    url(r'^(?P<club_id>[0-9]+)/sellings$', ClubSellingView.as_view(), name='club_sellings'),
    url(r'^(?P<club_id>[0-9]+)/sellings/csv$', ClubSellingCSVView.as_view(), name='sellings_csv'),
    url(r'^(?P<club_id>[0-9]+)/prop$', ClubEditPropView.as_view(), name='club_prop'),
    url(r'^(?P<club_id>[0-9]+)/tools$', ClubToolsView.as_view(), name='tools'),
    url(r'^membership/(?P<membership_id>[0-9]+)/set_old$', MembershipSetOldView.as_view(), name='membership_set_old'),
]

