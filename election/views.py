from typing import TYPE_CHECKING

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from core.auth.mixins import CanCreateMixin, CanEditMixin, CanViewMixin
from core.views.forms import SelectDateTime
from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultipleGroup,
    AutoCompleteSelectUser,
)
from core.views.widgets.markdown import MarkdownInput
from election.models import Candidature, Election, ElectionList, Role, Vote

if TYPE_CHECKING:
    from core.models import User


# Custom form field


class LimitedCheckboxField(forms.ModelMultipleChoiceField):
    """A `ModelMultipleChoiceField`, with a max limit of selectable inputs."""

    def __init__(self, queryset, max_choice, **kwargs):
        self.max_choice = max_choice
        super().__init__(queryset, **kwargs)

    def clean(self, value):
        qs = super().clean(value)
        self.validate(qs)
        return qs

    def validate(self, qs):
        if qs.count() > self.max_choice:
            raise forms.ValidationError(
                _("You have selected too much candidates."), code="invalid"
            )


# Forms


class CandidateForm(forms.ModelForm):
    """Form to candidate."""

    class Meta:
        model = Candidature
        fields = ["user", "role", "program", "election_list"]
        labels = {
            "user": _("User to candidate"),
        }
        widgets = {
            "program": MarkdownInput,
            "user": AutoCompleteSelectUser,
            "role": AutoCompleteSelect,
            "election_list": AutoCompleteSelect,
        }

    def __init__(self, *args, **kwargs):
        election_id = kwargs.pop("election_id", None)
        can_edit = kwargs.pop("can_edit", False)
        super().__init__(*args, **kwargs)
        if election_id:
            self.fields["role"].queryset = Role.objects.filter(
                election__id=election_id
            ).all()
            self.fields["election_list"].queryset = ElectionList.objects.filter(
                election__id=election_id
            ).all()
        if not can_edit:
            self.fields["user"].widget = forms.HiddenInput()


class VoteForm(forms.Form):
    def __init__(self, election, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not election.has_voted(user):
            for role in election.roles.all():
                cand = role.candidatures
                if role.max_choice > 1:
                    self.fields[role.title] = LimitedCheckboxField(
                        cand, role.max_choice, required=False
                    )
                else:
                    self.fields[role.title] = forms.ModelChoiceField(
                        cand,
                        required=False,
                        widget=forms.RadioSelect(),
                        empty_label=_("Blank vote"),
                    )


class RoleForm(forms.ModelForm):
    """Form for creating a role."""

    class Meta:
        model = Role
        fields = ["title", "election", "description", "max_choice"]
        widgets = {"election": AutoCompleteSelect}

    def __init__(self, *args, **kwargs):
        election_id = kwargs.pop("election_id", None)
        super().__init__(*args, **kwargs)
        if election_id:
            self.fields["election"].queryset = Election.objects.filter(
                id=election_id
            ).all()

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        election = cleaned_data.get("election")
        if Role.objects.filter(title=title, election=election).exists():
            raise forms.ValidationError(
                _("This role already exists for this election"), code="invalid"
            )


class ElectionListForm(forms.ModelForm):
    class Meta:
        model = ElectionList
        fields = ("title", "election")
        widgets = {"election": AutoCompleteSelect}

    def __init__(self, *args, **kwargs):
        election_id = kwargs.pop("election_id", None)
        super().__init__(*args, **kwargs)
        if election_id:
            self.fields["election"].queryset = Election.objects.filter(
                id=election_id
            ).all()


class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = [
            "title",
            "description",
            "archived",
            "start_candidature",
            "end_candidature",
            "start_date",
            "end_date",
            "edit_groups",
            "view_groups",
            "vote_groups",
            "candidature_groups",
        ]
        widgets = {
            "edit_groups": AutoCompleteSelectMultipleGroup,
            "view_groups": AutoCompleteSelectMultipleGroup,
            "vote_groups": AutoCompleteSelectMultipleGroup,
            "candidature_groups": AutoCompleteSelectMultipleGroup,
        }

    start_date = forms.DateTimeField(
        label=_("Start date"), widget=SelectDateTime, required=True
    )
    end_date = forms.DateTimeField(
        label=_("End date"), widget=SelectDateTime, required=True
    )
    start_candidature = forms.DateTimeField(
        label=_("Start candidature"), widget=SelectDateTime, required=True
    )
    end_candidature = forms.DateTimeField(
        label=_("End candidature"), widget=SelectDateTime, required=True
    )


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
        return super().dispatch(request, *arg, **kwargs)

    def get_initial(self):
        init = {}
        self.can_edit = self.request.user.can_edit(self.election)
        init["user"] = self.request.user.id
        return init

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election_id"] = self.election.id
        kwargs["can_edit"] = self.can_edit
        return kwargs

    def form_valid(self, form):
        """Verify that the selected user is in candidate group."""
        obj = form.instance
        obj.election = self.election
        if not hasattr(obj, "user"):
            obj.user = self.request.user
        if (obj.election.can_candidate(obj.user)) and (
            obj.user == self.request.user or self.can_edit
        ):
            return super().form_valid(form)
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["election"] = self.election
        return kwargs

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


class CandidatureUpdateView(CanEditMixin, UpdateView):
    model = Candidature
    form_class = CandidateForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "candidature_id"

    def dispatch(self, request, *arg, **kwargs):
        self.object = self.get_object()
        if not self.object.role.election.is_vote_editable:
            raise PermissionDenied
        return super().dispatch(request, *arg, **kwargs)

    def remove_fields(self):
        self.form.fields.pop("role", None)

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        self.remove_fields()
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, request, *args, **kwargs):
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
        kwargs["election_id"] = self.object.role.election.id
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "election:detail", kwargs={"election_id": self.object.role.election.id}
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
