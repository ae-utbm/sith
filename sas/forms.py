import copy
import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image

from core.models import User
from core.utils import resize_image
from core.views import MultipleImageField
from core.views.forms import SelectDate
from core.views.widgets.ajax_select import AutoCompleteSelectMultipleGroup
from sas.models import Album, Picture, PictureModerationRequest
from sas.widgets.ajax_select import AutoCompleteSelectAlbum

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile


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
        widgets = {"edit_groups": AutoCompleteSelectMultipleGroup, "date": SelectDate}

    name = forms.CharField(max_length=Album.NAME_MAX_LENGTH, label=_("file name"))
    recursive = forms.BooleanField(label=_("Apply rights recursively"), required=False)
    parent = forms.ModelChoiceField(
        Album.objects.all(), required=True, widget=AutoCompleteSelectAlbum
    )

    def clean_date(self):
        album_date: datetime.date = self.cleaned_data["date"]
        return datetime.datetime(
            year=album_date.year,
            month=album_date.month,
            day=album_date.day,
            tzinfo=get_current_timezone(),
        )

    def clean_file(self):
        # if a file was given in the form, resize it
        f: FieldFile = self.cleaned_data["file"]
        if self.errors or not f or "file" not in self.changed_data:
            return f
        f.file = resize_image(Image.open(f.file), 200, "WEBP")
        return f

    def save(self, commit=True):  # noqa: FBT002
        initial_file = copy.copy(self.initial["file"])
        if not self.cleaned_data["file"]:
            # if no file is in the form, it can mean either :
            # - there was a file initially, but the deletion box was checked
            # - there was no file initially, and there still isn't
            # in both cases, we procedurally generate the thumbnail
            self.instance.generate_thumbnail()
        elif "file" in self.changed_data:
            # the file was either added or modified
            self.instance.file.name = str(Path(self.instance.name) / "thumb.webp")
        res = super().save(commit=commit)
        if initial_file and (
            not self.instance.file or initial_file.path != self.instance.file.path
        ):
            # The initial file must be removed from storage
            # AFTER the new one has been dealt with,
            # in order to be sure that django will generate a different filename.
            # Otherwise, the client cache wouldn't be properly busted.
            initial_file.delete(save=False)
        return res


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
