from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django import forms
from django.contrib.auth import logout, login, authenticate
from django.forms import CheckboxSelectMultiple
import logging

from core.models import User, Page, Group

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


class UserGroupsForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = User
        fields = ['groups', 'user_permissions',]
        widgets = {
            'groups': CheckboxSelectMultiple,
            'user_permissions': CheckboxSelectMultiple,
        }

class GroupEditForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Group
        fields = ['name', 'permissions',]
        widgets = {
            'permissions': CheckboxSelectMultiple,
        }

