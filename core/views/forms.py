#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr> #
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
import re
from copy import copy
from datetime import date, datetime
from io import BytesIO

from captcha.fields import CaptchaField
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.management.commands.collectstatic import (
    staticfiles_storage,
)
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import (
    CheckboxSelectMultiple,
    DateInput,
    DateTimeInput,
    TextInput,
)
from django.utils.timezone import localtime, now
from django.utils.translation import gettext_lazy as _
from phonenumber_field.widgets import RegionalPhoneNumberWidget
from PIL import Image

from antispam.forms import AntiSpamEmailField
from core.models import Gift, Group, Page, PageRev, SithFile, User
from core.utils import resize_image
from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectGroup,
    AutoCompleteSelectMultipleGroup,
    AutoCompleteSelectUser,
)
from core.views.widgets.markdown import MarkdownInput

# Widgets


class SelectDateTime(DateTimeInput):
    def __init__(self, attrs=None, format=None):  # noqa A002
        default = {"type": "datetime-local"}
        attrs = default if attrs is None else default | attrs
        super().__init__(attrs=attrs, format=format or "%Y-%m-%d %H:%M")


class SelectDate(DateInput):
    def __init__(self, attrs=None, format=None):  # noqa A002
        default = {"type": "date"}
        attrs = default if attrs is None else default | attrs
        super().__init__(attrs=attrs, format=format or "%Y-%m-%d")


class NFCTextInput(TextInput):
    template_name = "core/widgets/nfc.jinja"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["statics"] = {
            "js": staticfiles_storage.url("bundled/core/components/nfc-input-index.ts"),
            "css": staticfiles_storage.url("core/components/nfc-input.scss"),
        }
        return context


# Fields


def validate_future_timestamp(value: date | datetime):
    if value <= now():
        raise ValidationError(_("Ensure this timestamp is set in the future"))


class FutureDateTimeField(forms.DateTimeField):
    """A datetime field that accepts only future timestamps."""

    default_validators = [validate_future_timestamp]

    def widget_attrs(self, widget: forms.Widget) -> dict[str, str]:
        return {"min": widget.format_value(localtime())}


# Forms


class LoginForm(AuthenticationForm):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.fields["username"].label = _("Username, email, or account number")

    def clean_username(self):
        identifier: str = self.cleaned_data["username"]
        account_code = re.compile(r"^[0-9]+[A-Za-z]$")
        if account_code.match(identifier):
            qs_filter = "customer__account_id__iexact"
        elif identifier.count("@") == 1:
            qs_filter = "email"
        else:
            qs_filter = None
        if qs_filter:
            # if the user gave an email or an account code instead of
            # a username, retrieve and return the corresponding username.
            # If there is no username, return an empty string, so that
            # Django will properly handle the error when failing the authentication
            identifier = (
                User.objects.filter(**{qs_filter: identifier})
                .values_list("username", flat=True)
                .first()
                or ""
            )
        return identifier


class RegisteringForm(UserCreationForm):
    error_css_class = "error"
    required_css_class = "required"
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        field_classes = {"email": AntiSpamEmailField}


class UserProfileForm(forms.ModelForm):
    """Form handling the user profile, managing the files"""

    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "nick_name",
            "email",
            "date_of_birth",
            "profile_pict",
            "avatar_pict",
            "scrub_pict",
            "sex",
            "pronouns",
            "second_email",
            "address",
            "parent_address",
            "phone",
            "parent_phone",
            "tshirt_size",
            "role",
            "department",
            "dpt_option",
            "semester",
            "quote",
            "school",
            "promo",
            "forum_signature",
            "is_viewable",
        ]
        widgets = {
            "date_of_birth": SelectDate,
            "phone": RegionalPhoneNumberWidget,
            "parent_phone": RegionalPhoneNumberWidget,
            "quote": forms.Textarea,
        }

    def __init__(self, *args, label_suffix: str = "", **kwargs):
        super().__init__(*args, label_suffix=label_suffix, **kwargs)

        # Image fields are injected here to override the file field provided by the model
        # This would be better if we could have a SithImage sort of model input instead of a generic SithFile
        self.fields["profile_pict"] = forms.ImageField(
            required=False,
            label=_(
                "Profile: you need to be visible on the picture, in order to be recognized (e.g. by the barmen)"
            ),
        )
        self.fields["avatar_pict"] = forms.ImageField(
            required=False,
            label=_("Avatar: used on the forum"),
        )
        self.fields["scrub_pict"] = forms.ImageField(
            required=False,
            label=_("Scrub: let other know how your scrub looks like!"),
        )

    def process(self, files):
        avatar = self.instance.avatar_pict
        profile = self.instance.profile_pict
        scrub = self.instance.scrub_pict
        self.full_clean()
        self.cleaned_data["avatar_pict"] = avatar
        self.cleaned_data["profile_pict"] = profile
        self.cleaned_data["scrub_pict"] = scrub
        parent = SithFile.objects.filter(parent=None, name="profiles").first()
        for field, f in files:
            with transaction.atomic():
                try:
                    im = Image.open(BytesIO(f.read()))
                    new_file = SithFile(
                        parent=parent,
                        name=f"{field.removesuffix('_pict')}_{self.instance.id}.webp",
                        file=resize_image(im, 400, "webp"),
                        owner=self.instance,
                        is_folder=False,
                        mime_type="image/wepb",
                        size=f.size,
                        moderator=self.instance,
                        is_moderated=True,
                    )
                    new_file.file.name = new_file.name
                    old = SithFile.objects.filter(
                        parent=parent, name=new_file.name
                    ).first()
                    if old:
                        old.delete()
                    new_file.clean()
                    new_file.save()
                    self.cleaned_data[field] = new_file
                    self._errors.pop(field, None)
                except ValidationError as e:
                    self._errors.pop(field, None)
                    self.add_error(
                        field,
                        _("Error uploading file %(file_name)s: %(msg)s")
                        % {"file_name": f, "msg": str(e.message)},
                    )
                except IOError:
                    self._errors.pop(field, None)
                    self.add_error(
                        field,
                        _("Error uploading file %(file_name)s: %(msg)s")
                        % {
                            "file_name": f,
                            "msg": _(
                                "Bad image format, only jpeg, png, webp and gif are accepted"
                            ),
                        },
                    )
        self._post_clean()


class UserGroupsForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(is_manually_manageable=True),
        widget=CheckboxSelectMultiple,
        label=_("Groups"),
        required=False,
    )

    class Meta:
        model = User
        fields = ["groups"]

    def save(self, *args, **kwargs) -> User:
        # make the super method manage error without persisting in db
        super().save(commit=False)
        # Don't forget to add the non-manageable groups when setting groups,
        # or the user would lose all of those when the form is submitted
        self.instance.groups.set(
            [
                *self.cleaned_data["groups"],
                *self.instance.groups.filter(is_manually_manageable=False),
            ]
        )
        return self.instance


class UserGodfathersForm(forms.Form):
    type = forms.ChoiceField(
        choices=[
            ("godfather", _("Godfather / Godmother")),
            ("godchild", _("Godchild")),
        ],
        label=_("Add"),
    )
    user = forms.ModelChoiceField(
        label=_("Select user"),
        help_text=None,
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_user = user

    def clean_user(self):
        other_user = self.cleaned_data.get("user")
        if not other_user:
            raise ValidationError(_("This user does not exist"))
        if other_user == self.target_user:
            raise ValidationError(_("You cannot be related to yourself"))
        return other_user

    def clean(self):
        super().clean()
        if not self.is_valid():
            return self.cleaned_data
        other_user = self.cleaned_data["user"]
        if self.cleaned_data["type"] == "godfather":
            if self.target_user.godfathers.contains(other_user):
                self.add_error(
                    "user",
                    _("%s is already your godfather") % (other_user.get_short_name()),
                )
        else:
            if self.target_user.godchildren.contains(other_user):
                self.add_error(
                    "user",
                    _("%s is already your godchild") % (other_user.get_short_name()),
                )
        return self.cleaned_data


class PagePropForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = Page
        fields = ["parent", "name", "owner_group", "edit_groups", "view_groups"]
        widgets = {
            "parent": AutoCompleteSelect,
            "owner_group": AutoCompleteSelectGroup,
            "edit_groups": AutoCompleteSelectMultipleGroup,
            "view_groups": AutoCompleteSelectMultipleGroup,
        }

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.fields["edit_groups"].required = False
        self.fields["view_groups"].required = False


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["parent", "name", "owner_group", "edit_groups", "view_groups"]
        widgets = {
            "parent": AutoCompleteSelect,
            "owner_group": AutoCompleteSelectGroup,
            "edit_groups": AutoCompleteSelectMultipleGroup,
            "view_groups": AutoCompleteSelectMultipleGroup,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = (
            self.fields["parent"]
            .queryset.exclude(name=settings.SITH_CLUB_ROOT_PAGE)
            .filter(club=None)
        )


class PageRevisionForm(forms.ModelForm):
    """Form to add a new revision to a page.

    Notes:
        Saving this form won't always result in a new revision.
        If the previous revision on the same page was made :

        - less than 20 minutes ago
        - by the same author
        - with a similarity ratio higher than 80%

        then the latter will be edited and the new revision won't be created.
    """

    class Meta:
        model = PageRev
        fields = ["title", "content"]
        widgets = {"content": MarkdownInput}

    def __init__(
        self, *args, author: User, page: Page, instance: PageRev | None = None, **kwargs
    ):
        super().__init__(*args, instance=instance, **kwargs)
        self.author = author
        self.page = page
        self.initial_obj: PageRev = copy(self.instance)

    def save(self, commit=True):  # noqa FBT002
        revision: PageRev = self.instance
        if not self.initial_obj.should_merge(self.instance):
            revision.author = self.author
            revision.page = self.page
            revision.id = None  # if id is None, Django will create a new record
        return super().save(commit=commit)


class GiftForm(forms.ModelForm):
    class Meta:
        model = Gift
        fields = ["label", "user"]

    label = forms.ChoiceField(choices=settings.SITH_GIFT_LIST)

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop("user_id", None)
        super().__init__(*args, **kwargs)
        if user_id:
            self.fields["user"].queryset = self.fields["user"].queryset.filter(
                id=user_id
            )
            self.fields["user"].widget = forms.HiddenInput()


class PermissionGroupsForm(forms.ModelForm):
    """Manage the groups that have a specific permission."""

    class Meta:
        model = Permission
        fields = []

    groups = forms.ModelMultipleChoiceField(
        Group.objects.all(),
        label=_("Groups"),
        widget=AutoCompleteSelectMultipleGroup,
        required=False,
    )

    def __init__(self, instance: Permission, **kwargs):
        super().__init__(instance=instance, **kwargs)
        self.fields["groups"].initial = instance.group_set.all()

    def save(self, commit: bool = True):  # noqa FTB001
        instance = super().save(commit=False)
        if commit:
            instance.group_set.set(self.cleaned_data["groups"])
        return instance
