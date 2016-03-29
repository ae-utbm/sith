from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django import forms
from django.contrib.auth import logout, login, authenticate
from django.forms import CheckboxSelectMultiple
import logging

from core.models import User, Page, RealGroup

class RegisteringForm(UserCreationForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'date_of_birth')

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
        fields = ['groups', 'edit_groups', 'view_groups']
        labels = {
            'edit_groups': "Edit profile group",
            'view_groups': "View profile group",
        }
        help_texts = {
            'edit_groups': "Groups that can edit this user's profile",
            'view_groups': "Groups that can view this user's profile",
            'groups': "Which groups this user belongs to",
        }
        widgets = {
            'groups': CheckboxSelectMultiple,
            'user_permissions': CheckboxSelectMultiple,
            'edit_groups': CheckboxSelectMultiple,
            'view_groups': CheckboxSelectMultiple,
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


class GroupEditForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = RealGroup
        fields = ['name', 'permissions',]
        widgets = {
            'permissions': CheckboxSelectMultiple,
        }

