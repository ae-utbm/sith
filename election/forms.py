from django import forms
from django.utils.translation import gettext_lazy as _

from club.forms import ClubRoleChoiceField
from club.models import ClubRole
from club.widgets.ajax_select import AutoCompleteSelectMultipleClub
from core.models import User
from core.views.forms import SelectDateTime
from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultipleGroup,
    AutoCompleteSelectUser,
)
from core.views.widgets.markdown import MarkdownInput
from election.models import Candidature, Election, ElectionList, Role


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
                _("You have selected too many candidates."), code="invalid"
            )


class CandidateForm(forms.ModelForm):
    """Form to candidate."""

    required_css_class = "required"

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

    def __init__(self, *args, election: Election, can_edit: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = election.roles.select_related("election")
        self.fields["election_list"].queryset = election.election_lists.all()
        if not can_edit:
            self.fields["user"].widget = forms.HiddenInput()


class VoteForm(forms.Form):
    def __init__(self, election: Election, user: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                    blank=True,
                )


class RoleForm(forms.ModelForm):
    """Form for creating a role."""

    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = Role
        fields = ["club_role", "title", "description", "max_choice"]
        field_classes = {"club_role": ClubRoleChoiceField}

    def __init__(self, *args, election: Election, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.election = election
        self.fields["club_role"].queryset = ClubRole.objects.filter(
            is_board=True, club__in=election.clubs.all()
        )

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

    def __init__(self, *args, election: Election, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.election = election


class ElectionForm(forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = Election
        fields = [
            "title",
            "description",
            "clubs",
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
            "clubs": AutoCompleteSelectMultipleClub,
            "edit_groups": AutoCompleteSelectMultipleGroup,
            "view_groups": AutoCompleteSelectMultipleGroup,
            "vote_groups": AutoCompleteSelectMultipleGroup,
            "candidature_groups": AutoCompleteSelectMultipleGroup,
            "start_date": SelectDateTime,
            "end_date": SelectDateTime,
            "start_candidature": SelectDateTime,
            "end_candidature": SelectDateTime,
        }
