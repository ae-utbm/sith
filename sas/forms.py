from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.views import MultipleImageField
from core.views.forms import SelectDate
from core.views.widgets.ajax_select import AutoCompleteSelectMultipleGroup
from sas.models import Album, Picture, PictureModerationRequest
from sas.widgets.ajax_select import AutoCompleteSelectAlbum


class AlbumCreateForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ["name", "parent"]
        labels = {"name": _("Add a new album")}
        widgets = {"parent": forms.HiddenInput}

    def __init__(self, *args, owner: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.owner = owner
        if owner.has_perm("sas.moderate_sasfile"):
            self.instance.is_moderated = True
            self.instance.moderator = owner

    def clean(self):
        parent = self.cleaned_data["parent"]
        parent.__class__ = Album  # by default, parent is a SithFile
        if not self.instance.owner.can_edit(parent):
            raise ValidationError(_("You do not have the permission to do that"))
        return super().clean()


class PictureUploadForm(forms.Form):
    images = MultipleImageField(label=_("Upload images"), required=False)


class PictureEditForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = ["name", "parent"]
        widgets = {"parent": AutoCompleteSelectAlbum}


class AlbumEditForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ["name", "date", "file", "parent", "edit_groups"]
        widgets = {
            "parent": AutoCompleteSelectAlbum,
            "edit_groups": AutoCompleteSelectMultipleGroup,
        }

    name = forms.CharField(max_length=Album.NAME_MAX_LENGTH, label=_("file name"))
    date = forms.DateField(label=_("Date"), widget=SelectDate, required=True)
    recursive = forms.BooleanField(label=_("Apply rights recursively"), required=False)


class PictureModerationRequestForm(forms.ModelForm):
    """Form to create a PictureModerationRequest.

    The form only manages the reason field,
    because the author and the picture are set in the view.
    """

    class Meta:
        model = PictureModerationRequest
        fields = ["reason"]

    def __init__(self, *args, user: User, picture: Picture, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.picture = picture

    def clean(self) -> dict[str, Any]:
        if PictureModerationRequest.objects.filter(
            author=self.user, picture=self.picture
        ).exists():
            raise forms.ValidationError(
                _("You already requested moderation for this picture.")
            )
        return super().clean()

    def save(self, *, commit=True) -> PictureModerationRequest:
        self.instance.author = self.user
        self.instance.picture = self.picture
        return super().save(commit)
