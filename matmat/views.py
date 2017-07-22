# -*- coding:utf-8 -*
#
# Copyright 2017
# - Sli <skia@libskia.so>
#
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

from django.shortcuts import render

# Create your views here.

from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import CheckboxSelectMultiple
from django import forms

from core.models import User
from core.views import WasSuscribed
from core.views.forms import SelectDate
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

# Custom form


class SearchForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'nick_name',
            'sex',
            'role',
            'department',
            'semester',
            'promo',
            'date_of_birth',
            'phone',
        ]
        widgets = {
            'date_of_birth': SelectDate,
            'phone': PhoneNumberInternationalFallbackWidget,
            # 'sex': CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        for key in self.fields.keys():
            self.fields[key].required = False
        self.fields['sex'].choices.append(("INDIFFERENT", _("Indifferent")))


# Views

class SearchFormListView(WasSuscribed, SingleObjectMixin, ListView):
    model = User
    template_name = 'matmat/search_form.jinja'

    def dispatch(self, request, *args, **kwargs):
        self.form_class = kwargs['form']
        self.reverse = kwargs['reverse']
        if 'valid_form' in kwargs.keys():
            self.valid_form = kwargs['valid_form']
        else:
            self.valid_form = None

        self.init_query = self.model.objects
        if not (request.user.is_board_member or request.user.is_root):
            self.init_query = self.init_query.exclude(is_subscriber_viewable=False)

        return super(SearchFormListView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.object = None
        kwargs = super(SearchFormListView, self).get_context_data(**kwargs)
        kwargs['form'] = self.form_class()
        return kwargs

    def get_queryset(self):
        if self.valid_form is not None:
            if self.reverse:
                return self.init_query.filter(phone=self.valid_form['phone']).all()
            else:
                q = self.init_query
                # f = self.valid_form
                return q.all()
        else:
            return self.model.objects.none()


class SearchFormView(WasSuscribed, FormView):
    """
    Allows users to search inside the user list
    """
    form_class = SearchForm
    reverse = False

    def dispatch(self, request, *args, **kwargs):
        self.init_query = User.objects
        kwargs['form'] = self.get_form_class()
        kwargs['reverse'] = self.reverse
        return super(SearchFormView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        view = SearchFormListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        view = SearchFormListView.as_view()
        if form.is_valid():
            kwargs['valid_form'] = form.clean()
        return view(request, *args, **kwargs)

    def get_initial(self):
        return super(SearchFormView, self).get_initial()


class SearchReverseFormView(SearchFormView):
    reverse = True
