from datetime import timedelta
from itertools import groupby, islice
from operator import attrgetter

from django import forms
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue
from django.utils.timezone import localdate, localtime
from django.utils.translation import gettext_lazy as _

from club.forms import ClubRoleChoiceField
from club.models import ClubRole, Membership
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


class ElectionCreateForm(ElectionForm):
    """ElectionForm, but specifically for creation."""

    def __init__(self, *args, initial: dict | None = None, **kwargs):
        # propose sound default timestamps :
        # start of candidatures at tomorrow 00h01, start of votes a week later.
        start = localtime().replace(hour=0, minute=1, second=0) + timedelta(days=1)
        default_initial = {
            "start_candidature": start,
            "end_candidature": start + timedelta(days=7, minutes=-2),  # 23h59
            "start_date": start + timedelta(days=7),  # 00h01
            "end_date": start + timedelta(days=14, minutes=-2),  # 23h59
            "view_groups": [settings.SITH_GROUP_PUBLIC_ID],
            "vote_groups": [settings.SITH_GROUP_SUBSCRIBERS_ID],
            "candidature_groups": [settings.SITH_GROUP_SUBSCRIBERS_ID],
        }
        if initial:
            default_initial.update(initial)
        super().__init__(*args, initial=default_initial, **kwargs)

    def save(self, commit=True):  # noqa: FBT002
        instance = super().save(commit=commit)
        if commit:
            ElectionList.objects.create(title="Candidat⸱e libre", election=instance)
        return instance


class ElectionWinnerChoiceIterator(ModelChoiceIterator):
    """Iterate over the candidates that gathered enough votes"""

    def __iter__(self):
        # for each role, yield only the N first candidates,
        # where N is the election role max_choice
        qs = (
            self.queryset.annotate(nb_votes=Count("votes"))
            .order_by("role__order", "-nb_votes")
            .select_related("role", "user", "role__club_role", "role__club_role__club")
        )
        yield from (
            (
                f"{role.title} \u2013 {role.club_role.club.name}",
                [self.choice(cand) for cand in islice(candidates, role.max_choice)],
            )
            for role, candidates in groupby(qs, key=attrgetter("role"))
        )

    def choice(self, obj: Candidature):
        return (
            ModelChoiceIteratorValue(self.field.prepare_value(obj), obj),
            obj.user.get_full_name(),
        )


class ElectionWinnerChoiceField(forms.ModelMultipleChoiceField):
    """Custom `ModelChoiceField` for `[ClubRole][club.models.ClubRole]`.

    If only one club is involved, behave like the base `ModelChoiceField`.
    If dealing with the roles of multiple clubs, group the roles
    into a different `optgroup` for each club.
    """

    iterator = ElectionWinnerChoiceIterator
    widget = forms.CheckboxSelectMultiple


class ApplyElectionResultForm(forms.Form):
    """Form to select winners of an election, and automatically apply the results."""

    candidates = ElectionWinnerChoiceField(Candidature.objects.none())

    def __init__(self, *args, election: Election, **kwargs):
        self.election = election
        super().__init__(*args, **kwargs)
        qs = Candidature.objects.filter(
            role__election=election, role__club_role__isnull=False
        )
        # pass all candidates to the ModelChoiceField ;
        # its inner choice iterator will take care of filtering only the winners.
        self.fields["candidates"].queryset = qs
        # By default, mark every candidate as selected.
        # Election results are usually completely validated during the AG,
        # so it makes more sense UX-wise to eventually unselect a candidate
        # than to select everyone.
        self.fields["candidates"].initial = qs.values_list("id", flat=True)

    def save(self):
        if self.errors:
            return
        candidates: list[Candidature] = list(self.cleaned_data["candidates"])
        with transaction.atomic():
            Membership.objects.filter(
                role__in=[c.role.club_role for c in candidates],
                end_date=None,
                start_date__lt=self.election.end_date,
            ).update(end_date=localdate())
            memberships = [
                Membership(
                    user_id=c.user_id,
                    club_id=c.role.club_role.club_id,
                    role=c.role.club_role,
                )
                for c in candidates
            ]
            Membership.objects.bulk_create(memberships)
            Membership._add_club_groups(memberships)
