#
# Copyright 2017
# - Sli <antoine@bartuccio.fr>
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
from enum import Enum

from django import forms
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from core.models import User
from core.views import FormerSubscriberMixin, search_user
from core.views.forms import SelectDate

# Enum to select search type


class SearchType(Enum):
    NORMAL = 1
    REVERSE = 2
    QUICK = 3


# Custom form


class SearchForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "nick_name",
            "role",
            "department",
            "semester",
            "promo",
            "date_of_birth",
            "phone",
        ]
        widgets = {
            "date_of_birth": SelectDate,
            "phone": RegionalPhoneNumberWidget,
        }

    quick = forms.CharField(label=_("Last/First name or nickname"), max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            self.fields[key].required = False

    @property
    def cleaned_data_json(self):
        data = self.cleaned_data
        for key in data.keys():
            if key in ("date_of_birth", "phone") and data[key] is not None:
                data[key] = str(data[key])
        return data


# Views


class SearchFormListView(FormerSubscriberMixin, SingleObjectMixin, ListView):
    model = User
    ordering = ["-id"]
    paginate_by = 12
    template_name = "matmat/search_form.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.form_class = kwargs["form"]
        self.search_type = kwargs["search_type"]
        self.session = request.session
        self.last_search = self.session.get("matmat_search_result", str([]))
        self.last_search = literal_eval(self.last_search)
        if "valid_form" in kwargs.keys():
            self.valid_form = kwargs["valid_form"]
        else:
            self.valid_form = None

        self.init_query = self.model.objects
        self.can_see_hidden = True
        if not (request.user.is_board_member or request.user.is_root):
            self.can_see_hidden = False
            self.init_query = self.init_query.exclude(is_subscriber_viewable=False)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.object = None
        kwargs = super().get_context_data(**kwargs)
        kwargs["form"] = self.form_class
        kwargs["result_exists"] = self.result_exists
        return kwargs

    def get_queryset(self):
        q = self.init_query
        if self.valid_form is not None:
            if self.search_type == SearchType.REVERSE:
                q = q.filter(phone=self.valid_form["phone"]).all()
            elif self.search_type == SearchType.QUICK:
                if self.valid_form["quick"].strip():
                    q = search_user(self.valid_form["quick"])
                else:
                    q = []
                if not self.can_see_hidden and len(q) > 0:
                    q = [user for user in q if user.is_subscriber_viewable]
            else:
                search_dict = {}
                for key, value in self.valid_form.items():
                    if key not in ("phone", "quick") and not (
                        value == "" or value is None
                    ):
                        search_dict[key + "__icontains"] = value
                q = q.filter(**search_dict).all()
        else:
            q = q.filter(pk__in=self.last_search).all()
        if isinstance(q, list):
            self.result_exists = len(q) > 0
        else:
            self.result_exists = q.exists()
        self.last_search = []
        for user in q:
            self.last_search.append(user.id)
        self.session["matmat_search_result"] = str(self.last_search)
        return q


class SearchFormView(FormerSubscriberMixin, FormView):
    """Allows users to search inside the user list."""

    form_class = SearchForm

    def dispatch(self, request, *args, **kwargs):
        self.session = request.session
        self.init_query = User.objects
        kwargs["form"] = self.get_form()
        kwargs["search_type"] = self.search_type
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        view = SearchFormListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        view = SearchFormListView.as_view()
        if form.is_valid():
            kwargs["valid_form"] = form.clean()
            request.session["matmat_search_form"] = form.cleaned_data_json
        return view(request, *args, **kwargs)

    def get_initial(self):
        init = self.session.get("matmat_search_form", {})
        if not init:
            init["department"] = ""
        return init


class SearchNormalFormView(SearchFormView):
    search_type = SearchType.NORMAL


class SearchReverseFormView(SearchFormView):
    search_type = SearchType.REVERSE


class SearchQuickFormView(SearchFormView):
    search_type = SearchType.QUICK


class SearchClearFormView(FormerSubscriberMixin, View):
    """Clear SearchFormView and redirect to it."""

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        if "matmat_search_form" in request.session.keys():
            request.session.pop("matmat_search_form")
        if "matmat_search_result" in request.session.keys():
            request.session.pop("matmat_search_result")
        return HttpResponseRedirect(reverse("matmat:search"))
