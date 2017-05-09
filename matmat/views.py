# -*- coding:utf-8 -*
#
# Copyright 2017
# - Skia <skia@libskia.so>
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

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView, SingleObjectMixin
from django.utils.translation import ugettext_lazy as _
from django import forms

from matmat.models import Matmat, MatmatUser
from core.views.forms import SelectFile, SelectDate
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin, CanCreateMixin, QuickNotifMixin
from core.models import User
from club.models import Club

class MatmatForm(forms.ModelForm):
    class Meta:
        model = Matmat
        fields = ['subscription_deadline', 'comments_deadline']
        widgets = {
                'subscription_deadline': SelectDate,
                'comments_deadline': SelectDate,
                }

class MatmatCreateView(CanEditPropMixin, CreateView):
    """
    Create a matmat for a club
    """
    model = Matmat
    form_class = MatmatForm
    template_name = 'core/create.jinja'

    def post(self, request, *args, **kwargs):
        """
        Affect club
        """
        form = self.get_form()
        if form.is_valid():
            club = get_object_or_404(Club, id=self.kwargs['club_id'])
            form.instance.club = club
            ret = self.form_valid(form)
            return ret
        else:
            return self.form_invalid(form)

class MatmatEditView(CanEditPropMixin, UpdateView):
    model = Matmat
    form_class = MatmatForm
    template_name = 'core/edit.jinja'
    pk_url_kwarg = 'matmat_id'

class MatmatDetailView(CanViewMixin, DetailView):
    model = Matmat
    template_name = 'matmat/detail.jinja'
    pk_url_kwarg = 'matmat_id'

class MatmatDeleteUserView(CanEditPropMixin, SingleObjectMixin, RedirectView):
    model = Matmat
    pk_url_kwarg = 'matmat_id'
    permanent = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = get_object_or_404(MatmatUser, id=self.kwargs['user_id'])
        user.delete()
# See if we need to also delete the comments on the user, or if we keep them
        return redirect(self.object.get_absolute_url())

# User side
class UserMatmatForm(forms.Form):
    matmat = forms.ModelChoiceField(Matmat.availables.all(), required=False, label=_("Select matmatronch"),
            help_text=_("This allows you to subscribe to a Matmatronch. "
            "Be aware that you can subscribe only once, so don't play with that, "
            "or you will expose yourself to the admins' wrath!"))

class UserMatmatView(QuickNotifMixin, TemplateView):
    """
    Display a user's matmat tools
    """
    template_name = "core/user_matmat.jinja"

    def post(self, request, *args, **kwargs):
        self.form = UserMatmatForm(request.POST)
        if self.form.is_valid():
            matmat_user = MatmatUser(user=request.user,
                    matmat=self.form.cleaned_data['matmat'])
            matmat_user.save()
            self.quick_notif_list += ['qn_success']
        return super(UserMatmatView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(UserMatmatView, self).get_context_data(**kwargs)
        kwargs['user'] = self.request.user
        if not hasattr(self.request.user, 'matmat_user'):
            kwargs['subscribe_form'] = UserMatmatForm()
        return kwargs

