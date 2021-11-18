# -*- coding:utf-8 -*
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
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
from captcha.fields import CaptchaField
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.conf import settings
from django.db import transaction
from django.templatetags.static import static
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.forms import (
    CheckboxSelectMultiple,
    Select,
    DateInput,
    TextInput,
    DateTimeInput,
    Textarea,
)
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget
from ajax_select.fields import AutoCompleteSelectField
from ajax_select import make_ajax_field
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import datetime
from django.forms.utils import to_current_timezone

import re

from core.models import User, Page, SithFile, Gift

from core.utils import resize_image
from io import BytesIO
from PIL import Image


# Widgets


class SelectDateTime(DateTimeInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs:
            attrs["class"] = "select_datetime"
        else:
            attrs = {"class": "select_datetime"}
        return super(SelectDateTime, self).render(name, value, attrs, renderer)


class SelectDate(DateInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs:
            attrs["class"] = "select_date"
        else:
            attrs = {"class": "select_date"}
        return super(SelectDate, self).render(name, value, attrs, renderer)


class MarkdownInput(Textarea):
    template_name = "core/markdown_textarea.jinja"

    def get_context(self, name, value, attrs):
        context = super(MarkdownInput, self).get_context(name, value, attrs)

        context["statics"] = {
            "js": static("core/easymde/easymde.min.js"),
            "css": static("core/easymde/easymde.min.css"),
        }
        context["translations"] = {
            "heading_smaller": _("Heading"),
            "italic": _("Italic"),
            "bold": _("Bold"),
            "strikethrough": _("Strikethrough"),
            "underline": _("Underline"),
            "superscript": _("Superscript"),
            "subscript": _("Subscript"),
            "code": _("Code"),
            "quote": _("Quote"),
            "unordered_list": _("Unordered list"),
            "ordered_list": _("Ordered list"),
            "image": _("Insert image"),
            "link": _("Insert link"),
            "table": _("Insert table"),
            "clean_block": _("Clean block"),
            "preview": _("Toggle preview"),
            "side_by_side": _("Toggle side by side"),
            "fullscreen": _("Toggle fullscreen"),
            "guide": _("Markdown guide"),
        }
        context["markdown_api_url"] = reverse("api:api_markdown")
        return context


class SelectFile(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs:
            attrs["class"] = "select_file"
        else:
            attrs = {"class": "select_file"}
        output = '%(content)s<div name="%(name)s" class="choose_file_widget" title="%(title)s"></div>' % {
            "content": super(SelectFile, self).render(name, value, attrs, renderer),
            "title": _("Choose file"),
            "name": name,
        }
        output += (
            '<span name="'
            + name
            + '" class="choose_file_button">'
            + ugettext("Choose file")
            + "</span>"
        )
        return output


class SelectUser(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs:
            attrs["class"] = "select_user"
        else:
            attrs = {"class": "select_user"}
        output = '%(content)s<div name="%(name)s" class="choose_user_widget" title="%(title)s"></div>' % {
            "content": super(SelectUser, self).render(name, value, attrs, renderer),
            "title": _("Choose user"),
            "name": name,
        }
        output += (
            '<span name="'
            + name
            + '" class="choose_user_button">'
            + ugettext("Choose user")
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
        super(LoginForm, self).__init__(*arg, **kwargs)
        self.fields["username"].label = _("Username, email, or account number")


class RegisteringForm(UserCreationForm):
    error_css_class = "error"
    required_css_class = "required"
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(RegisteringForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.generate_username()
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form handling the user profile, managing the files
    This form is actually pretty bad and was made in the rush before the migration. It should be refactored.
    TODO: refactor this form
    """

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
            "profile_pict": forms.ClearableFileInput,
            "avatar_pict": forms.ClearableFileInput,
            "scrub_pict": forms.ClearableFileInput,
            "phone": PhoneNumberInternationalFallbackWidget,
            "parent_phone": PhoneNumberInternationalFallbackWidget,
        }
        labels = {
            "profile_pict": _(
                "Profile: you need to be visible on the picture, in order to be recognized (e.g. by the barmen)"
            ),
            "avatar_pict": _("Avatar: used on the forum"),
            "scrub_pict": _("Scrub: let other know how your scrub looks like!"),
        }

    def __init__(self, *arg, **kwargs):
        super(UserProfileForm, self).__init__(*arg, **kwargs)

    def full_clean(self):
        super(UserProfileForm, self).full_clean()

    def generate_name(self, field_name, f):
        field_name = field_name[:-4]
        return field_name + str(self.instance.id) + "." + f.content_type.split("/")[-1]

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
                        name=self.generate_name(field, f),
                        file=resize_image(im, 400, f.content_type.split("/")[-1]),
                        owner=self.instance,
                        is_folder=False,
                        mime_type=f.content_type,
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
                                "Bad image format, only jpeg, png, and gif are accepted"
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
        choices=[("godfather", _("Godfather")), ("godchild", _("Godchild"))],
        label=_("Add"),
    )
    user = AutoCompleteSelectField(
        "users", required=True, label=_("Select user"), help_text=None
    )


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
        super(PagePropForm, self).__init__(*arg, **kwargs)
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
        super(PageForm, self).__init__(*args, **kwargs)
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
        super(GiftForm, self).__init__(*args, **kwargs)
        if user_id:
            self.fields["user"].queryset = self.fields["user"].queryset.filter(
                id=user_id
            )
            self.fields["user"].widget = forms.HiddenInput()


class TzAwareDateTimeField(forms.DateTimeField):
    def __init__(
        self, input_formats=["%Y-%m-%d %H:%M:%S"], widget=SelectDateTime, **kwargs
    ):
        super().__init__(input_formats=input_formats, widget=widget, **kwargs)

    def prepare_value(self, value):
        # the db value is a datetime as a string in UTC
        if isinstance(value, str):
            # convert it into a naive datetime (no timezone attached)
            value = parse_datetime(value)
            # attach it to the UTC timezone (so that to_current_timezone()) if not None
            # converts it to the local timezone)
            if value is not None:
                value = timezone.make_aware(value, timezone.utc)

        if isinstance(value, datetime.datetime):
            value = to_current_timezone(value)
            # otherwise it is formatted according to locale (in french)
            value = str(value)

        return value
