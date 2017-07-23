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
from ast import literal_eval

from django.views.generic import ListView, View
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin
from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse
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
        }

    sex = forms.ChoiceField([
        ("MAN", _("Man")),
        ("WOMAN", _("Woman")),
        ("INDIFFERENT", _("Indifferent"))
    ], widget=forms.RadioSelect, initial="INDIFFERENT")

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        for key in self.fields.keys():
            self.fields[key].required = False

    @property
    def cleaned_data_json(self):
        data = self.cleaned_data
        for key in data.keys():
            if key in ('date_of_birth', 'phone') and data[key] is not None:
                data[key] = str(data[key])
        return data

# Views


class SearchFormListView(WasSuscribed, SingleObjectMixin, ListView):
    model = User
    template_name = 'matmat/search_form.jinja'
    paginate_by = 3

    def dispatch(self, request, *args, **kwargs):
        self.form_class = kwargs['form']
        self.reverse = kwargs['reverse']
        self.session = request.session
        self.last_search = self.session.get('matmat_search_result', str([]))
        self.last_search = literal_eval(self.last_search)
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
        kwargs['form'] = self.form_class
        kwargs['result_exists'] = self.result_exists
        return kwargs

    def get_queryset(self):
        q = self.init_query
        if self.valid_form is not None:
            if self.reverse:
                q = q.filter(phone=self.valid_form['phone']).all()
            else:
                search_dict = {}
                for key, value in self.valid_form.items():
                    if key != 'phone' and not (value == '' or value is None or value == 'INDIFFERENT'):
                        search_dict[key + "__icontains"] = value
                q = q.filter(**search_dict).all()
        else:
            q = q.filter(pk__in=self.last_search).all()
        self.result_exists = q.exists()
        self.last_search = []
        for user in q:
            self.last_search.append(user.id)
        self.session['matmat_search_result'] = str(self.last_search)
        return q


class SearchFormView(WasSuscribed, FormView):
    """
    Allows users to search inside the user list
    """
    form_class = SearchForm
    reverse = False

    def dispatch(self, request, *args, **kwargs):
        self.session = request.session
        self.init_query = User.objects
        kwargs['form'] = self.get_form()
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
            request.session['matmat_search_form'] = form.cleaned_data_json
        return view(request, *args, **kwargs)

    def get_initial(self):
        return self.session.get('matmat_search_form', {})


class SearchReverseFormView(SearchFormView):
    reverse = True


class SearchClearFormView(WasSuscribed, View):
    """
    Clear SearchFormView and redirect to it
    """

    def dispatch(self, request, *args, **kwargs):
        super(SearchClearFormView, self).dispatch(request, *args, **kwargs)
        if 'matmat_search_form' in request.session.keys():
            request.session.pop('matmat_search_form')
        if 'matmat_search_result' in request.session.keys():
            request.session.pop('matmat_search_result')
        return HttpResponseRedirect(reverse('matmat:search'))
