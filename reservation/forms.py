from django import forms

from club.widgets.ajax_select import AutoCompleteSelectClub
from core.models import User
from core.views.forms import FutureDateTimeField, SelectDateTime
from reservation.models import ReservationSlot, Room


class RoomCreateForm(forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = Room
        fields = ["name", "club", "location", "description"]
        widgets = {"club": AutoCompleteSelectClub}


class RoomUpdateForm(forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = Room
        fields = ["name", "club", "location", "description"]
        widgets = {"club": AutoCompleteSelectClub}

    def __init__(self, *args, request_user: User, **kwargs):
        super().__init__(*args, **kwargs)
        if not request_user.has_perm("reservation.change_room"):
            # if the user doesn't have the global edition permission
            # (i.e. it's a club board member, but not a sith admin)
            # some fields aren't editable
            del self.fields["club"]


class ReservationForm(forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = ReservationSlot
        fields = ["room", "start_at", "end_at", "comment"]
        field_classes = {"start_at": FutureDateTimeField, "end_at": FutureDateTimeField}
        widgets = {"start_at": SelectDateTime(), "end_at": SelectDateTime()}

    def __init__(self, *args, author: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author

    def save(self, commit: bool = True):  # noqa FBT001
        self.instance.author = self.author
        return super().save(commit)
