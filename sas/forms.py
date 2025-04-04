from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.views import MultipleImageField
from core.views.forms import SelectDate
from core.views.widgets.ajax_select import AutoCompleteSelectMultipleGroup
from sas.models import Album, Picture, PictureModerationRequest
from sas.widgets.ajax_select import AutoCompleteSelectAlbum


class SASForm(forms.Form):
    album_name = forms.CharField(
        label=_("Add a new album"), max_length=Album.NAME_MAX_LENGTH, required=False
    )
    images = MultipleImageField(
        label=_("Upload images"),
        required=False,
    )

    def process(self, parent, owner, files, *, automodere=False):
        try:
            if self.cleaned_data["album_name"] != "":
                album = Album(
                    parent=parent,
                    name=self.cleaned_data["album_name"],
                    owner=owner,
                    is_moderated=automodere,
                )
                album.clean()
                album.save()
        except Exception as e:
            self.add_error(
                None,
                _("Error creating album %(album)s: %(msg)s")
                % {"album": self.cleaned_data["album_name"], "msg": repr(e)},
            )
        for f in files:
            new_file = Picture(
                parent=parent,
                name=f.name,
                file=f,
                owner=owner,
                mime_type=f.content_type,
                size=f.size,
                is_folder=False,
                is_moderated=automodere,
            )
            if automodere:
                new_file.moderator = owner
            try:
                new_file.clean()
                new_file.generate_thumbnails()
                new_file.save()
            except Exception as e:
                self.add_error(
                    None,
                    _("Error uploading file %(file_name)s: %(msg)s")
                    % {"file_name": f, "msg": repr(e)},
                )


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
