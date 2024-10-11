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
from io import BytesIO

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectField
from captcha.fields import CaptchaField
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import (
    CheckboxSelectMultiple,
    DateInput,
    DateTimeInput,
    Textarea,
    TextInput,
)
from django.templatetags.static import static
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from phonenumber_field.widgets import RegionalPhoneNumberWidget
from PIL import Image

from antispam.forms import AntiSpamEmailField
from core.models import Gift, Page, SithFile, User
from core.utils import resize_image

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


class MarkdownInput(Textarea):
    template_name = "core/widgets/markdown_textarea.jinja"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["statics"] = {
            "js": static("webpack/easymde-index.js"),
            "css": static("webpack/easymde-index.css"),
        }
        return context


class NFCTextInput(TextInput):
    template_name = "core/widgets/nfc.jinja"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["translations"] = {"unsupported": _("Unsupported NFC card")}
        return context


class SelectFile(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs:
            attrs["class"] = "select_file"
        else:
            attrs = {"class": "select_file"}
        output = (
            '%(content)s<div name="%(name)s" class="choose_file_widget" title="%(title)s"></div>'
            % {
                "content": super().render(name, value, attrs, renderer),
                "title": _("Choose file"),
                "name": name,
            }
        )
        output += (
            '<span name="'
            + name
            + '" class="choose_file_button">'
            + gettext("Choose file")
            + "</span>"
        )
        return output


class SelectUser(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs:
            attrs["class"] = "select_user"
        else:
            attrs = {"class": "select_user"}
        output = (
            '%(content)s<div name="%(name)s" class="choose_user_widget" title="%(title)s"></div>'
            % {
                "content": super().render(name, value, attrs, renderer),
                "title": _("Choose user"),
                "name": name,
            }
        )
        output += (
            '<span name="'
            + name
            + '" class="choose_user_button">'
            + gettext("Choose user")
            + "</span>"
        )
        return output


# Forms


class LoginForm(AuthenticationForm):
    def __init__(self, *arg, **kwargs):
        if "data" in kwargs.keys():
            from counter.models import Customer

            data = kwargs["data"].copy()
            account_code = re.compile(r"^[0-9]+[A-Za-z]$")
            try:
                if account_code.match(data["username"]):
                    user = (
                        Customer.objects.filter(account_id__iexact=data["username"])
                        .first()
                        .user
                    )
                elif "@" in data["username"]:
                    user = User.objects.filter(email__iexact=data["username"]).first()
                else:
                    user = User.objects.filter(username=data["username"]).first()
                data["username"] = user.username
            except:
                pass
            kwargs["data"] = data
        super().__init__(*arg, **kwargs)
        self.fields["username"].label = _("Username, email, or account number")


class RegisteringForm(UserCreationForm):
    error_css_class = "error"
    required_css_class = "required"
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        field_classes = {
            "email": AntiSpamEmailField,
        }


class UserProfileForm(forms.ModelForm):
    """Form handling the user profile, managing the files"""

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
            "is_subscriber_viewable",
        ]
        widgets = {
            "date_of_birth": SelectDate,
            "phone": RegionalPhoneNumberWidget,
            "parent_phone": RegionalPhoneNumberWidget,
            "quote": forms.Textarea,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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


class UserPropForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = User
        fields = ["groups"]
        help_texts = {"groups": "Which groups this user belongs to"}
        widgets = {"groups": CheckboxSelectMultiple}


class UserGodfathersForm(forms.Form):
    type = forms.ChoiceField(
        choices=[
            ("godfather", _("Godfather / Godmother")),
            ("godchild", _("Godchild")),
        ],
        label=_("Add"),
    )
    user = AutoCompleteSelectField(
        "users", required=True, label=_("Select user"), help_text=""
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

    edit_groups = make_ajax_field(
        Page, "edit_groups", "groups", help_text="", label=_("edit groups")
    )
    view_groups = make_ajax_field(
        Page, "view_groups", "groups", help_text="", label=_("view groups")
    )

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.fields["edit_groups"].required = False
        self.fields["view_groups"].required = False


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["parent", "name", "owner_group", "edit_groups", "view_groups"]

    edit_groups = make_ajax_field(
        Page, "edit_groups", "groups", help_text="", label=_("edit groups")
    )
    view_groups = make_ajax_field(
        Page, "view_groups", "groups", help_text="", label=_("view groups")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = (
            self.fields["parent"]
            .queryset.exclude(name=settings.SITH_CLUB_ROOT_PAGE)
            .filter(club=None)
        )


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
