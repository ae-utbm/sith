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
from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView, SingleObjectMixin
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.models import modelform_factory

from trombi.models import Trombi, TrombiUser, TrombiComment
from core.views.forms import SelectFile, SelectDate
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin, CanCreateMixin, QuickNotifMixin
from core.models import User
from club.models import Club

class TrombiForm(forms.ModelForm):
    class Meta:
        model = Trombi
        fields = ['subscription_deadline', 'comments_deadline', 'max_chars']
        widgets = {
                'subscription_deadline': SelectDate,
                'comments_deadline': SelectDate,
                }

class TrombiCreateView(CanEditPropMixin, CreateView):
    """
    Create a trombi for a club
    """
    model = Trombi
    form_class = TrombiForm
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

class TrombiEditView(CanEditPropMixin, UpdateView):
    model = Trombi
    form_class = TrombiForm
    template_name = 'core/edit.jinja'
    pk_url_kwarg = 'trombi_id'

    def get_success_url(self):
        return super(TrombiEditView, self).get_success_url()+"?qn_success"

class TrombiDetailView(CanEditMixin, QuickNotifMixin, DetailView):
    model = Trombi
    template_name = 'trombi/detail.jinja'
    pk_url_kwarg = 'trombi_id'

class TrombiDeleteUserView(CanEditPropMixin, SingleObjectMixin, RedirectView):
    model = Trombi
    pk_url_kwarg = 'trombi_id'
    permanent = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = get_object_or_404(TrombiUser, id=self.kwargs['user_id'])
        user.delete()
# See if we need to also delete the comments on the user, or if we keep them
        return redirect(self.object.get_absolute_url()+"?qn_success")

# User side
class UserTrombiForm(forms.Form):
    trombi = forms.ModelChoiceField(Trombi.availables.all(), required=False, label=_("Select trombi"),
            help_text=_("This allows you to subscribe to a Trombi. "
            "Be aware that you can subscribe only once, so don't play with that, "
            "or you will expose yourself to the admins' wrath!"))

class UserTrombiToolsView(QuickNotifMixin, TemplateView):
    """
    Display a user's trombi tools
    """
    template_name = "trombi/user_tools.jinja"

    def post(self, request, *args, **kwargs):
        self.form = UserTrombiForm(request.POST)
        if self.form.is_valid():
            trombi_user = TrombiUser(user=request.user,
                    trombi=self.form.cleaned_data['trombi'])
            trombi_user.save()
            self.quick_notif_list += ['qn_success']
        return super(UserTrombiToolsView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(UserTrombiToolsView, self).get_context_data(**kwargs)
        kwargs['user'] = self.request.user
        if not hasattr(self.request.user, 'trombi_user'):
            kwargs['subscribe_form'] = UserTrombiForm()
        return kwargs

class UserTrombiEditPicturesView(UpdateView):
    model = TrombiUser
    fields = ['profile_pict', 'scrub_pict']
    template_name = "core/edit.jinja"

    def get_object(self):
        return self.request.user.trombi_user

    def get_success_url(self):
        return reverse('trombi:user_tools')+"?qn_success"

class UserTrombiEditProfileView(UpdateView):
    model = User
    form_class = modelform_factory(User,
            fields=['second_email', 'phone', 'department', 'dpt_option',
                'quote', 'parent_address'],
            labels={
                'second_email': _("Personal email (not UTBM)"),
                'phone': _("Phone"),
                'parent_address': _("Native town"),
            })
    template_name = "core/edit.jinja"

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('trombi:user_tools')+"?qn_success"

class TrombiCommentFormView():
    """
    Create/edit a trombi comment
    """
    model = TrombiComment
    fields = ['content']
    template_name = 'trombi/comment.jinja'

    def get_form_class(self):
        self.trombi = self.request.user.trombi_user.trombi
        return modelform_factory(self.model, fields=self.fields,
            widgets={
                'content': forms.widgets.Textarea(attrs={'maxlength': self.trombi.max_chars})
            },
            help_texts={
                'content': _("Maximum characters: %(max_length)s") % {'max_length': self.trombi.max_chars}
            })

    def get_success_url(self):
        return reverse('trombi:user_tools')+"?qn_success"

    def get_context_data(self, **kwargs):
        kwargs = super(TrombiCommentFormView, self).get_context_data(**kwargs)
        if 'user_id' in self.kwargs.keys():
            kwargs['target'] = get_object_or_404(TrombiUser, id=self.kwargs['user_id'])
        else:
            kwargs['target'] = self.object.target
        return kwargs

class TrombiCommentCreateView(TrombiCommentFormView, CreateView):
    def form_valid(self, form):
        target = get_object_or_404(TrombiUser, id=self.kwargs['user_id'])
        form.instance.author = self.request.user.trombi_user
        form.instance.target = target
        return super(TrombiCommentCreateView, self).form_valid(form)

class TrombiCommentEditView(TrombiCommentFormView, CanViewMixin, UpdateView):
    pk_url_kwarg = "comment_id"


