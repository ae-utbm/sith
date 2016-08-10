from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django import forms
from django.contrib.auth import logout, login, authenticate
from django.forms import CheckboxSelectMultiple, Select
from django.utils.translation import ugettext as _
import logging

from core.models import User, Page, RealGroup

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

class SelectFile(Select):
    def render(self, name, value, attrs=None):
        output = '<span class="choose_file_widget" title="%(title)s">%(content)s</span>' % {
                'title': _("Choose file"),
                'content': super(SelectFile, self).render(name, value, attrs),
                }
        output += '<span class="choose_file_button">' + _("Choose file") + '</span>'
        print(output)
        return output

