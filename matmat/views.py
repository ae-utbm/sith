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

from django.db.models import F
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from core.auth.mixins import FormerSubscriberMixin
from core.models import User, UserQuerySet
from core.schemas import UserFilterSchema
from matmat.forms import SearchForm


class MatmatronchView(FormerSubscriberMixin, FormMixin, ListView):
    model = User
    paginate_by = 20
    template_name = "matmat/search_form.jinja"
    form_class = SearchForm

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        return self.request.GET

    def get_form_kwargs(self):
        res = super().get_form_kwargs()
        if self.request.GET:
            res["data"] = self.request.GET
        return res

    def get_queryset(self) -> UserQuerySet:
        if not self.form.is_valid():
            return User.objects.none()
        data = self.form.cleaned_data
        data["search"] = data.get("name")
        filters = UserFilterSchema(**{key: val for key, val in data.items() if val})
        qs = User.objects.viewable_by(self.request.user).select_related("profile_pict")
        return filters.filter(qs).order_by(F("last_login").desc(nulls_last=True))

    def get_context_data(self, **kwargs):
        return super().get_context_data(form=self.form, **kwargs)
