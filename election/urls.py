from django.urls import path

from election.views import (
    CandidatureCreateView,
    CandidatureDeleteView,
    CandidatureUpdateView,
    ElectionCreateView,
    ElectionDeleteView,
    ElectionDetailView,
    ElectionListArchivedView,
    ElectionListCreateView,
    ElectionListDeleteView,
    ElectionsListView,
    ElectionUpdateView,
    RoleCreateView,
    RoleDeleteView,
    RoleUpdateView,
    VoteFormView,
)

urlpatterns = [
    path("", ElectionsListView.as_view(), name="list"),
    path("archived/", ElectionListArchivedView.as_view(), name="list_archived"),
    path("add/", ElectionCreateView.as_view(), name="create"),
    path("<int:election_id>/edit/", ElectionUpdateView.as_view(), name="update"),
    path("<int:election_id>/delete/", ElectionDeleteView.as_view(), name="delete"),
    path(
        "<int:election_id>/list/add/",
        ElectionListCreateView.as_view(),
        name="create_list",
    ),
    path(
        "<int:list_id>/list/delete/",
        ElectionListDeleteView.as_view(),
        name="delete_list",
    ),
    path(
        "<int:election_id>/role/create/", RoleCreateView.as_view(), name="create_role"
    ),
    path("<int:role_id>/role/edit/", RoleUpdateView.as_view(), name="update_role"),
    path("<int:role_id>/role/delete/", RoleDeleteView.as_view(), name="delete_role"),
    path(
        "<int:election_id>/candidate/add/",
        CandidatureCreateView.as_view(),
        name="candidate",
    ),
    path(
        "<int:candidature_id>/candidate/edit/",
        CandidatureUpdateView.as_view(),
        name="update_candidate",
    ),
    path(
        "<int:candidature_id>/candidate/delete/",
        CandidatureDeleteView.as_view(),
        name="delete_candidate",
    ),
    path("<int:election_id>/vote/", VoteFormView.as_view(), name="vote"),
    path("<int:election_id>/detail/", ElectionDetailView.as_view(), name="detail"),
]
