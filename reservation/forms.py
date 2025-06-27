from django import forms

from club.widgets.ajax_select import AutoCompleteSelectClub
from core.models import User
from reservation.models import Room


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
