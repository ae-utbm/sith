from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import logout, login, authenticate
from django.forms import CheckboxSelectMultiple, Select, DateInput, TextInput
from django.utils.translation import ugettext as _
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

import logging

from core.models import User, Page, RealGroup, SithFile


# Widgets

class SelectSingle(Select):
    def render(self, name, value, attrs=None):
        if attrs:
            attrs['class'] = "select_single"
        else:
            attrs = {'class': "select_single"}
        return super(SelectSingle, self).render(name, value, attrs)

class SelectMultiple(Select):
    def render(self, name, value, attrs=None):
        if attrs:
            attrs['class'] = "select_multiple"
        else:
            attrs = {'class': "select_multiple"}
        return super(SelectMultiple, self).render(name, value, attrs)

class SelectDate(DateInput):
    def render(self, name, value, attrs=None):
        if attrs:
            attrs['class'] = "select_date"
        else:
            attrs = {'class': "select_date"}
        return super(SelectDate, self).render(name, value, attrs)

class SelectFile(TextInput):
    def render(self, name, value, attrs=None):
        if attrs:
            attrs['class'] = "select_file"
        else:
            attrs = {'class': "select_file"}
        output = '%(content)s<div name="%(name)s" class="choose_file_widget" title="%(title)s"></div>' % {
                'content': super(SelectFile, self).render(name, value, attrs),
                'title': _("Choose file"),
                'name': name,
                }
        output += '<span name="' + name + '" class="choose_file_button">' + _("Choose file") + '</span>'
        return output

# Forms

class RegisteringForm(UserCreationForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super(RegisteringForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.generate_username()
        if commit:
            user.save()
        return user

# Image utils

from io import BytesIO
from PIL import Image

def scale_dimension(width, height, long_edge):
    if width > height:
        ratio = long_edge * 1. / width
    else:
        ratio = long_edge * 1. / height
    return int(width * ratio), int(height * ratio)

def resize_image(im, edge, format):
    from django.core.files.base import ContentFile
    (w, h) = im.size
    (width, height) = scale_dimension(w, h, long_edge=edge)
    content = BytesIO()
    im.resize((width, height), Image.ANTIALIAS).save(fp=content, format=format, dpi=[72, 72])
    return ContentFile(content.getvalue())

class UserProfileForm(forms.ModelForm):
    """
    Form handling the user profile, managing the files
    This form is actually pretty bad and was made in the rush before the migration. It should be refactored.
    TODO: refactor this form
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'nick_name', 'email', 'date_of_birth', 'profile_pict', 'avatar_pict',
                'scrub_pict', 'sex', 'second_email', 'address', 'parent_address', 'phone', 'parent_phone',
                'tshirt_size', 'role', 'department', 'dpt_option', 'semester', 'quote', 'school', 'promo',
                'forum_signature']
        widgets = {
                'date_of_birth': SelectDate,
                'profile_pict': forms.ClearableFileInput,
                'avatar_pict': forms.ClearableFileInput,
                'scrub_pict': forms.ClearableFileInput,
                'phone': PhoneNumberInternationalFallbackWidget,
                'parent_phone': PhoneNumberInternationalFallbackWidget,
                }
        labels = {
                'profile_pict': _("Profile: you need to be visible on the picture, in order to be recognized (e.g. by the barmen)"),
                'avatar_pict': _("Avatar: used on the forum"),
                'scrub_pict': _("Scrub: let other know how your scrub looks like!"),
                }

    def __init__(self, *arg, **kwargs):
        super(UserProfileForm, self).__init__(*arg, **kwargs)

    def full_clean(self):
        super(UserProfileForm, self).full_clean()

    def generate_name(self, field_name, f):
        field_name = field_name[:-4]
        return field_name + str(self.instance.id) + "." + f.content_type.split('/')[-1]

    def process(self, files):
        avatar = self.instance.avatar_pict
        profile = self.instance.profile_pict
        scrub = self.instance.scrub_pict
        self.full_clean()
        self.cleaned_data['avatar_pict'] = avatar
        self.cleaned_data['profile_pict'] = profile
        self.cleaned_data['scrub_pict'] = scrub
        parent = SithFile.objects.filter(parent=None, name="profiles").first()
        for field,f in files:
            with transaction.atomic():
                try:
                    im = Image.open(BytesIO(f.read()))
                    new_file = SithFile(parent=parent, name=self.generate_name(field, f),
                            file=resize_image(im, 400, f.content_type.split('/')[-1]),
                            owner=self.instance, is_folder=False, mime_type=f.content_type, size=f._size)
                    new_file.file.name = new_file.name
                    old = SithFile.objects.filter(parent=parent, name=new_file.name).first()
                    if old:
                        old.delete()
                    new_file.clean()
                    new_file.save()
                    self.cleaned_data[field] = new_file
                    self._errors.pop(field, None)
                except ValidationError as e:
                    self._errors.pop(field, None)
                    self.add_error(field, _("Error uploading file %(file_name)s: %(msg)s") %
                            {'file_name': f, 'msg': str(e.message)})
                except IOError:
                    self._errors.pop(field, None)
                    self.add_error(field, _("Error uploading file %(file_name)s: %(msg)s") %
                            {'file_name': f, 'msg': _("Bad image format, only jpeg, png, and gif are accepted")})
        self._post_clean()

class UserPropForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = User
        fields = ['groups']
        help_texts = {
            'groups': "Which groups this user belongs to",
        }
        widgets = {
            'groups': CheckboxSelectMultiple,
        }

class PagePropForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Page
        fields = ['parent', 'name', 'owner_group', 'edit_groups', 'view_groups', ]
        widgets = {
            'edit_groups': CheckboxSelectMultiple,
            'view_groups': CheckboxSelectMultiple,
        }

    def __init__(self, *arg, **kwargs):
        super(PagePropForm, self).__init__(*arg, **kwargs)
        self.fields['edit_groups'].required = False
        self.fields['view_groups'].required = False

