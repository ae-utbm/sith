#
# Copyright 2025
# - Maréchal <thomas.girod@utbm.fr>
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
from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.views.forms import SelectDate


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
        widgets = {"date_of_birth": SelectDate}

    quick = forms.CharField(label=_("Last/First name or nickname"), max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = False

    @property
    def cleaned_data_json(self):
        data = self.cleaned_data
        if "date_of_birth" in data and data["date_of_birth"] is not None:
            data["date_of_birth"] = str(data["date_of_birth"])
        return data
