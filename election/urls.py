from django.conf.urls import url

from election.views import *

urlpatterns = [
    url(r"^$", ElectionsListView.as_view(), name="list"),
    url(r"^archived$", ElectionListArchivedView.as_view(), name="list_archived"),
    url(r"^add$", ElectionCreateView.as_view(), name="create"),
    url(r"^(?P<election_id>[0-9]+)/edit$", ElectionUpdateView.as_view(), name="update"),
    url(
        r"^(?P<election_id>[0-9]+)/delete$", ElectionDeleteView.as_view(), name="delete"
    ),
    url(
        r"^(?P<election_id>[0-9]+)/list/add$",
        ElectionListCreateView.as_view(),
        name="create_list",
    ),
    url(
        r"^(?P<list_id>[0-9]+)/list/delete$",
        ElectionListDeleteView.as_view(),
        name="delete_list",
    ),
    url(
        r"^(?P<election_id>[0-9]+)/role/create$",
        RoleCreateView.as_view(),
        name="create_role",
    ),
    url(
        r"^(?P<role_id>[0-9]+)/role/edit$", RoleUpdateView.as_view(), name="update_role"
    ),
    url(
        r"^(?P<role_id>[0-9]+)/role/delete$",
        RoleDeleteView.as_view(),
        name="delete_role",
    ),
    url(
        r"^(?P<election_id>[0-9]+)/candidate/add$",
        CandidatureCreateView.as_view(),
        name="candidate",
    ),
    url(
        r"^(?P<candidature_id>[0-9]+)/candidate/edit$",
        CandidatureUpdateView.as_view(),
        name="update_candidate",
    ),
    url(
        r"^(?P<candidature_id>[0-9]+)/candidate/delete$",
        CandidatureDeleteView.as_view(),
        name="delete_candidate",
    ),
    url(r"^(?P<election_id>[0-9]+)/vote$", VoteFormView.as_view(), name="vote"),
    url(
        r"^(?P<election_id>[0-9]+)/detail$", ElectionDetailView.as_view(), name="detail"
    ),
]
