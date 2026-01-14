from typing import TYPE_CHECKING

from cryptography.utils import cached_property
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from core.auth.mixins import CanEditMixin, CanViewMixin
from election.forms import (
    CandidateForm,
    ElectionForm,
    ElectionListForm,
    RoleForm,
    VoteForm,
)
from election.models import Candidature, Election, ElectionList, Role, Vote

if TYPE_CHECKING:
    from core.models import User


# Display elections


class ElectionsListView(CanViewMixin, ListView):
    """A list of all non archived elections visible."""

    model = Election
    queryset = model.objects.filter(archived=False)
    ordering = ["-id"]
    paginate_by = 10
    template_name = "election/election_list.jinja"


class ElectionListArchivedView(CanViewMixin, ListView):
    """A list of all archived elections visible."""

    model = Election
    queryset = model.objects.filter(archived=True)
    ordering = ["-id"]
    paginate_by = 10
    template_name = "election/election_list.jinja"


class ElectionDetailView(CanViewMixin, DetailView):
    """Details an election responsibility by responsibility."""

    model = Election
    template_name = "election/election_detail.jinja"
    pk_url_kwarg = "election_id"

    @staticmethod
    def _reorder_votes(action: str, role: int):
        role = Role.objects.filter(id=role).first()
        if not role:
            return
        if action == "up":
            role.up()
        elif action == "down":
            role.down()
        elif action == "bottom":
            role.bottom()
        elif action == "top":
            role.top()

    def get(self, request, *arg, **kwargs):
        election: Election = self.get_object()
        if election.is_vote_editable and request.user.can_edit(election):
            action = request.GET.get("action", None)
            role = request.GET.get("role", None)
            if action and role and role.isdigit():
                self._reorder_votes(action, int(role))
        return super().get(request, *arg, **kwargs)

    def get_context_data(self, **kwargs):
        """Add additional data to the template."""
        user: User = self.request.user
        return super().get_context_data(**kwargs) | {
            "election_form": VoteForm(self.object, user),
            "show_vote_buttons": self.object.can_vote(user),
            "user_has_voted": self.object.has_voted(user),
            "election_results": (
                self.object.results if self.object.is_vote_finished else None
            ),
            "election_lists": list(self.object.election_lists.all()),
            "election_roles": list(self.object.roles.order_by("order")),
        }


# Form view


class VoteFormView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Allows users to vote."""

    form_class = VoteForm
    template_name = "election/election_detail.jinja"

    @cached_property
    def election(self):
        return get_object_or_404(Election, pk=self.kwargs["election_id"])

    def test_func(self):
        if not self.election.can_vote(self.request.user):
            return False

        groups = set(self.election.vote_groups.values_list("id", flat=True))
        if (
            settings.SITH_GROUP_SUBSCRIBERS_ID in groups
            and self.request.user.is_subscribed
        ):
            # the subscriber group isn't truly attached to users,
            # so it must be dealt with separately
            return True
        return self.request.user.groups.filter(id__in=groups).exists()

    def vote(self, election_data):
        with transaction.atomic():
            for role_title in election_data:
                # If we have a multiple choice field
                if isinstance(election_data[role_title], QuerySet):
                    if election_data[role_title].count() > 0:
                        vote = Vote(role=election_data[role_title].first().role)
                        vote.save()
                    for el in election_data[role_title]:
                        vote.candidature.add(el)
                # If we have a single choice
                elif election_data[role_title] is not None:
                    vote = Vote(role=election_data[role_title].role)
                    vote.save()
                    vote.candidature.add(election_data[role_title])
            self.election.voters.add(self.request.user)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "election": self.election,
            "user": self.request.user,
        }

    def form_valid(self, form):
        """Verify that the user is part in a vote group."""
        data = form.clean()
        self.vote(data)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Form is invalid"))
        return redirect(
            reverse("election:detail", kwargs={"election_id": self.election.id}),
        )

    def get_success_url(self, **kwargs):
        return reverse_lazy("election:detail", kwargs={"election_id": self.election.id})

    def get_context_data(self, **kwargs):
        """Add additional data to the template."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["object"] = self.election
        kwargs["election"] = self.election
        kwargs["election_form"] = self.get_form()
        return kwargs


# Create views


class CandidatureCreateView(LoginRequiredMixin, CreateView):
    """View dedicated to a cundidature creation."""

    form_class = CandidateForm
    model = Candidature
    template_name = "election/candidate_form.jinja"

    def dispatch(self, request, *arg, **kwargs):
        self.election = get_object_or_404(Election, pk=kwargs["election_id"])
        self.can_edit = self.request.user.can_edit(self.election)
        return super().dispatch(request, *arg, **kwargs)

    def get_initial(self):
        return {"user": self.request.user.id}

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "election": self.election,
            "can_edit": self.can_edit,
        }

    def form_valid(self, form: CandidateForm):
        """Verify that the selected user is in candidate group."""
        obj = form.instance
        obj.election = self.election
        if (obj.election.can_candidate(obj.user)) and (
            obj.user == self.request.user or self.can_edit
        ):
            return super().form_valid(form)
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"election": self.election}

    def get_success_url(self, **kwargs):
        return reverse_lazy("election:detail", kwargs={"election_id": self.election.id})


class ElectionCreateView(PermissionRequiredMixin, CreateView):
    model = Election
    form_class = ElectionForm
    template_name = "core/create.jinja"
    permission_required = "election.add_election"

    def get_success_url(self, **kwargs):
        return reverse("election:detail", kwargs={"election_id": self.object.id})


class RoleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = "core/create.jinja"

    @cached_property
    def election(self):
        return get_object_or_404(Election, pk=self.kwargs["election_id"])

    def test_func(self):
        if not self.election.is_vote_editable:
            return False
        if self.request.user.has_perm("election.add_role"):
            return True
        groups = set(self.election.edit_groups.values_list("id", flat=True))
        if (
            settings.SITH_GROUP_SUBSCRIBERS_ID in groups
            and self.request.user.is_subscribed
        ):
            # the subscriber group isn't truly attached to users,
            # so it must be dealt with separately
            return True
        return self.request.user.groups.filter(id__in=groups).exists()

    def get_initial(self):
        return {"election": self.election}

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"election_id": self.election.id}

    def get_success_url(self, **kwargs):
        return reverse(
            "election:detail", kwargs={"election_id": self.object.election_id}
        )


class ElectionListCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ElectionList
    form_class = ElectionListForm
    template_name = "core/create.jinja"

    @cached_property
    def election(self):
        return get_object_or_404(Election, pk=self.kwargs["election_id"])

    def test_func(self):
        if not self.election.is_vote_editable:
            return False
        if self.request.user.has_perm("election.add_electionlist"):
            return True
        groups = set(
            self.election.candidature_groups.values("id")
            .union(self.election.edit_groups.values("id"))
            .values_list("id", flat=True)
        )
        if (
            settings.SITH_GROUP_SUBSCRIBERS_ID in groups
            and self.request.user.is_subscribed
        ):
            # the subscriber group isn't truly attached to users,
            # so it must be dealt with separately
            return True
        return self.request.user.groups.filter(id__in=groups).exists()

    def get_initial(self):
        return {"election": self.election}

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"election_id": self.election.id}

    def get_success_url(self, **kwargs):
        return reverse(
            "election:detail", kwargs={"election_id": self.object.election_id}
        )


# Update view


class ElectionUpdateView(CanEditMixin, UpdateView):
    model = Election
    form_class = ElectionForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "election_id"

    def get_initial(self):
        return {
            "start_date": self.object.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": self.object.end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "start_candidature": self.object.start_candidature.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "end_candidature": self.object.end_candidature.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    def get_success_url(self, **kwargs):
        return reverse_lazy("election:detail", kwargs={"election_id": self.object.id})


class CandidatureUpdateView(LoginRequiredMixin, CanEditMixin, UpdateView):
    model = Candidature
    form_class = CandidateForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "candidature_id"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields.pop("role", None)
        return form

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"election": self.object.role.election}

    def get_success_url(self, **kwargs):
        return reverse(
            "election:detail", kwargs={"election_id": self.object.role.election_id}
        )


class RoleUpdateView(CanEditMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "role_id"

    def dispatch(self, request, *arg, **kwargs):
        self.object = self.get_object()
        if not self.object.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *arg, **kwargs)

    def remove_fields(self):
        self.form.fields.pop("election", None)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        self.remove_fields()
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        self.remove_fields()
        if (
            request.user.is_authenticated
            and request.user.can_edit(self.object)
            and self.form.is_valid()
        ):
            return super().form_valid(self.form)
        return self.form_invalid(self.form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election_id"] = self.object.election.id
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "election:detail", kwargs={"election_id": self.object.election.id}
        )


# Delete Views


class ElectionDeleteView(PermissionRequiredMixin, DeleteView):
    model = Election
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "election_id"
    permission_required = "election.delete_election"
    success_url = reverse_lazy("election:list")


class CandidatureDeleteView(CanEditMixin, DeleteView):
    model = Candidature
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "candidature_id"

    def dispatch(self, request, *arg, **kwargs):
        self.object = self.get_object()
        self.election = self.object.role.election
        if not self.election.can_candidate or not self.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *arg, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse("election:detail", kwargs={"election_id": self.election.id})


class RoleDeleteView(CanEditMixin, DeleteView):
    model = Role
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "role_id"

    def dispatch(self, request, *arg, **kwargs):
        self.object = self.get_object()
        self.election = self.object.election
        if not self.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *arg, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse("election:detail", kwargs={"election_id": self.election.id})


class ElectionListDeleteView(CanEditMixin, DeleteView):
    model = ElectionList
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "list_id"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.election = self.object.election
        if not self.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse("election:detail", kwargs={"election_id": self.election.id})
