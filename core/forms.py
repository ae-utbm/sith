from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth import logout, login, authenticate
import logging

from .models import User, Page

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

class LoginForm(AuthenticationForm):
    def login(self):
        u = authenticate(username=self.request.POST['username'],
                         password=self.request.POST['password'])
        if u is not None:
            if u.is_active:
                login(self.request, u)
                logging.debug("Logging in "+str(u))
            else:
                raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='inactive',
                        params={'username': self.username_field.verbose_name},
                    )
        else:
            logging.debug("Login failed")
            raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )

class PageForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    parent = forms.ModelChoiceField(queryset=Page.objects.all())

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        self.fields['parent'].required = False

    class Meta:
        model = Page
        fields = ['parent', 'name', 'title', 'content', ]

    def save(self, commit=True):
        page = super(PageForm, self).save(commit=False)
        if commit:
            page.save()
        return page


