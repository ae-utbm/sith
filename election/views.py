from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from core.auth.mixins import CanCreateMixin, CanEditMixin, CanViewMixin
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
    ordering = ["-id"]
    paginate_by = 10
    template_name = "election/election_list.jinja"

    def get_queryset(self):
        return super().get_queryset().filter(archived=False).all()


class ElectionListArchivedView(CanViewMixin, ListView):
    """A list of all archived elections visible."""

    model = Election
    ordering = ["-id"]
    paginate_by = 10
    template_name = "election/election_list.jinja"

    def get_queryset(self):
        return super().get_queryset().filter(archived=True).all()


class ElectionDetailView(CanViewMixin, DetailView):
    """Details an election responsability by responsability."""

    model = Election
    template_name = "election/election_detail.jinja"
    pk_url_kwarg = "election_id"

    def get(self, request, *arg, **kwargs):
        response = super().get(request, *arg, **kwargs)
        election: Election = self.get_object()
        if request.user.can_edit(election) and election.is_vote_editable:
            action = request.GET.get("action", None)
            role = request.GET.get("role", None)
            if action and role and Role.objects.filter(id=role).exists():
                if action == "up":
                    Role.objects.get(id=role).up()
                elif action == "down":
                    Role.objects.get(id=role).down()
                elif action == "bottom":
                    Role.objects.get(id=role).bottom()
                elif action == "top":
                    Role.objects.get(id=role).top()
                return redirect(
                    reverse("election:detail", kwargs={"election_id": election.id})
                )
        return response

    def get_context_data(self, **kwargs):
        """Add additionnal data to the template."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["election_form"] = VoteForm(self.object, self.request.user)
        kwargs["election_results"] = self.object.results
        return kwargs


# Form view


class VoteFormView(CanCreateMixin, FormView):
    """Alows users to vote."""

    form_class = VoteForm
    template_name = "election/election_detail.jinja"

    def dispatch(self, request, *arg, **kwargs):
        self.election = get_object_or_404(Election, pk=kwargs["election_id"])
        return super().dispatch(request, *arg, **kwargs)

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
        kwargs = super().get_form_kwargs()
        kwargs["election"] = self.election
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Verify that the user is part in a vote group."""
        data = form.clean()
        res = super(FormView, self).form_valid(form)
        for grp_id in self.election.vote_groups.values_list("pk", flat=True):
            if self.request.user.is_in_group(pk=grp_id):
                self.vote(data)
                return res
        return res

    def get_success_url(self, **kwargs):
        return reverse_lazy("election:detail", kwargs={"election_id": self.election.id})

    def get_context_data(self, **kwargs):
        """Add additionnal data to the template."""
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


class RoleCreateView(CanCreateMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = "core/create.jinja"

    def dispatch(self, request, *arg, **kwargs):
        self.election = get_object_or_404(Election, pk=kwargs["election_id"])
        if not self.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *arg, **kwargs)

    def get_initial(self):
        init = {}
        init["election"] = self.election
        return init

    def form_valid(self, form):
        """Verify that the user can edit properly."""
        obj: Role = form.instance
        user: User = self.request.user
        if obj.election:
            for grp_id in obj.election.edit_groups.values_list("pk", flat=True):
                if user.is_in_group(pk=grp_id):
                    return super(CreateView, self).form_valid(form)
        raise PermissionDenied

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election_id"] = self.election.id
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "election:detail", kwargs={"election_id": self.object.election.id}
        )


class ElectionListCreateView(CanCreateMixin, CreateView):
    model = ElectionList
    form_class = ElectionListForm
    template_name = "core/create.jinja"

    def dispatch(self, request, *arg, **kwargs):
        self.election = get_object_or_404(Election, pk=kwargs["election_id"])
        if not self.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *arg, **kwargs)

    def get_initial(self):
        init = {}
        init["election"] = self.election
        return init

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election_id"] = self.election.id
        return kwargs

    def form_valid(self, form):
        """Verify that the user can vote on this election."""
        obj: ElectionList = form.instance
        user: User = self.request.user
        if obj.election:
            for grp_id in obj.election.candidature_groups.values_list("pk", flat=True):
                if user.is_in_group(pk=grp_id):
                    return super(CreateView, self).form_valid(form)
            for grp_id in obj.election.edit_groups.values_list("pk", flat=True):
                if user.is_in_group(pk=grp_id):
                    return super(CreateView, self).form_valid(form)
        raise PermissionDenied

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "election:detail", kwargs={"election_id": self.object.election.id}
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


class ElectionDeleteView(DeleteView):
    model = Election
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "election_id"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_root:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def get_success_url(self, **kwargs):
        return reverse_lazy("election:list")


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
        return reverse_lazy("election:detail", kwargs={"election_id": self.election.id})


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
        return reverse_lazy("election:detail", kwargs={"election_id": self.election.id})


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
        return reverse_lazy("election:detail", kwargs={"election_id": self.election.id})
