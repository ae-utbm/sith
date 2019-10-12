from django.urls import re_path

from election.views import *

urlpatterns = [
    re_path(r"^$", ElectionsListView.as_view(), name="list"),
    re_path(r"^archived$", ElectionListArchivedView.as_view(), name="list_archived"),
    re_path(r"^add$", ElectionCreateView.as_view(), name="create"),
    re_path(
        r"^(?P<election_id>[0-9]+)/edit$", ElectionUpdateView.as_view(), name="update"
    ),
    re_path(
        r"^(?P<election_id>[0-9]+)/delete$", ElectionDeleteView.as_view(), name="delete"
    ),
    re_path(
        r"^(?P<election_id>[0-9]+)/list/add$",
        ElectionListCreateView.as_view(),
        name="create_list",
    ),
    re_path(
        r"^(?P<list_id>[0-9]+)/list/delete$",
        ElectionListDeleteView.as_view(),
        name="delete_list",
    ),
    re_path(
        r"^(?P<election_id>[0-9]+)/role/create$",
        RoleCreateView.as_view(),
        name="create_role",
    ),
    re_path(
        r"^(?P<role_id>[0-9]+)/role/edit$", RoleUpdateView.as_view(), name="update_role"
    ),
    re_path(
        r"^(?P<role_id>[0-9]+)/role/delete$",
        RoleDeleteView.as_view(),
        name="delete_role",
    ),
    re_path(
        r"^(?P<election_id>[0-9]+)/candidate/add$",
        CandidatureCreateView.as_view(),
        name="candidate",
    ),
    re_path(
        r"^(?P<candidature_id>[0-9]+)/candidate/edit$",
        CandidatureUpdateView.as_view(),
        name="update_candidate",
    ),
    re_path(
        r"^(?P<candidature_id>[0-9]+)/candidate/delete$",
        CandidatureDeleteView.as_view(),
        name="delete_candidate",
    ),
    re_path(r"^(?P<election_id>[0-9]+)/vote$", VoteFormView.as_view(), name="vote"),
    re_path(
        r"^(?P<election_id>[0-9]+)/detail$", ElectionDetailView.as_view(), name="detail"
    ),
]
