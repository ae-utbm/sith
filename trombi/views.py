#
# Copyright 2017,2020
# - Skia <skia@libskia.so>
# - Sli <antoine.bartuccio@gmail.com>
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

from datetime import date

from ajax_select.fields import AutoCompleteSelectField
from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from club.models import Club
from core.models import User
from core.views import (
    CanCreateMixin,
    CanEditMixin,
    CanEditPropMixin,
    CanViewMixin,
    QuickNotifMixin,
    TabedViewMixin,
)
from core.views.forms import SelectDate
from trombi.models import Trombi, TrombiClubMembership, TrombiComment, TrombiUser


class TrombiTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return _("Trombi")

    def get_list_of_tabs(self):
        tab_list = []
        tab_list.append(
            {"url": reverse("trombi:user_tools"), "slug": "tools", "name": _("Tools")}
        )
        if hasattr(self.request.user, "trombi_user"):
            tab_list.append(
                {
                    "url": reverse("trombi:profile"),
                    "slug": "profile",
                    "name": _("My profile"),
                }
            )
            tab_list.append(
                {
                    "url": reverse("trombi:pictures"),
                    "slug": "pictures",
                    "name": _("My pictures"),
                }
            )
        try:
            trombi = self.request.user.trombi_user.trombi
            if self.request.user.is_owner(trombi):
                tab_list.append(
                    {
                        "url": reverse(
                            "trombi:detail", kwargs={"trombi_id": trombi.id}
                        ),
                        "slug": "admin_tools",
                        "name": _("Admin tools"),
                    }
                )
        except:
            pass
        return tab_list


class UserIsInATrombiMixin(View):
    """Check if the requested user has a trombi_user attribute."""

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self.request.user, "trombi_user"):
            raise Http404()

        return super().dispatch(request, *args, **kwargs)


class TrombiForm(forms.ModelForm):
    class Meta:
        model = Trombi
        fields = [
            "subscription_deadline",
            "comments_deadline",
            "max_chars",
            "show_profiles",
        ]
        widgets = {"subscription_deadline": SelectDate, "comments_deadline": SelectDate}


class TrombiCreateView(CanCreateMixin, CreateView):
    """Create a trombi for a club."""

    model = Trombi
    form_class = TrombiForm
    template_name = "core/create.jinja"

    def post(self, request, *args, **kwargs):
        """Affect club."""
        form = self.get_form()
        if form.is_valid():
            club = get_object_or_404(Club, id=self.kwargs["club_id"])
            form.instance.club = club
            ret = self.form_valid(form)
            return ret
        else:
            return self.form_invalid(form)


class TrombiEditView(CanEditPropMixin, TrombiTabsMixin, UpdateView):
    model = Trombi
    form_class = TrombiForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "trombi_id"
    current_tab = "admin_tools"

    def get_success_url(self):
        return super().get_success_url() + "?qn_success"


class AddUserForm(forms.Form):
    user = AutoCompleteSelectField(
        "users", required=True, label=_("Select user"), help_text=None
    )


class TrombiDetailView(CanEditMixin, QuickNotifMixin, TrombiTabsMixin, DetailView):
    model = Trombi
    template_name = "trombi/detail.jinja"
    pk_url_kwarg = "trombi_id"
    current_tab = "admin_tools"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AddUserForm(request.POST)
        if form.is_valid():
            try:
                TrombiUser(user=form.cleaned_data["user"], trombi=self.object).save()
                self.quick_notif_list.append("qn_success")
            except:  # We don't care about duplicate keys
                self.quick_notif_list.append("qn_fail")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["form"] = AddUserForm()
        return kwargs


class TrombiExportView(CanEditMixin, TrombiTabsMixin, DetailView):
    model = Trombi
    template_name = "trombi/export.jinja"
    pk_url_kwarg = "trombi_id"
    current_tab = "admin_tools"


class TrombiDeleteUserView(CanEditPropMixin, TrombiTabsMixin, DeleteView):
    model = TrombiUser
    pk_url_kwarg = "user_id"
    template_name = "core/delete_confirm.jinja"
    current_tab = "admin_tools"

    def get_success_url(self):
        return (
            reverse("trombi:detail", kwargs={"trombi_id": self.object.trombi.id})
            + "?qn_success"
        )


class TrombiModerateCommentsView(
    CanEditPropMixin, QuickNotifMixin, TrombiTabsMixin, DetailView
):
    model = Trombi
    template_name = "trombi/comment_moderation.jinja"
    pk_url_kwarg = "trombi_id"
    current_tab = "admin_tools"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["comments"] = TrombiComment.objects.filter(
            is_moderated=False, author__trombi__id=self.object.id
        ).exclude(target__user__id=self.request.user.id)
        return kwargs


class TrombiModerateForm(forms.Form):
    reason = forms.CharField(help_text=_("Explain why you rejected the comment"))
    action = forms.CharField(initial="delete", widget=forms.widgets.HiddenInput)


class TrombiModerateCommentView(DetailView):
    model = TrombiComment
    template_name = "core/edit.jinja"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_owner(self.object.author.trombi):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "action" in request.POST:
            if request.POST["action"] == "accept":
                self.object.is_moderated = True
                self.object.save()
                return redirect(
                    reverse(
                        "trombi:moderate_comments",
                        kwargs={"trombi_id": self.object.author.trombi.id},
                    )
                    + "?qn_success"
                )
            elif request.POST["action"] == "reject":
                return super().get(request, *args, **kwargs)
            elif request.POST["action"] == "delete" and "reason" in request.POST.keys():
                self.object.author.user.email_user(
                    subject="[%s] %s" % (settings.SITH_NAME, _("Rejected comment")),
                    message=_(
                        'Your comment to %(target)s on the Trombi "%(trombi)s" was rejected for the following '
                        "reason: %(reason)s\n\n"
                        "Your comment was:\n\n%(content)s"
                    )
                    % {
                        "target": self.object.target.user.get_display_name(),
                        "trombi": self.object.author.trombi,
                        "reason": request.POST["reason"],
                        "content": self.object.content,
                    },
                )
                self.object.delete()
                return redirect(
                    reverse(
                        "trombi:moderate_comments",
                        kwargs={"trombi_id": self.object.author.trombi.id},
                    )
                    + "?qn_success"
                )
        raise Http404

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["form"] = TrombiModerateForm()
        return kwargs


# User side


class TrombiModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return _("%(name)s (deadline: %(date)s)") % {
            "name": str(obj),
            "date": str(obj.subscription_deadline),
        }


class UserTrombiForm(forms.Form):
    trombi = TrombiModelChoiceField(
        Trombi.availables.all(),
        required=False,
        label=_("Select trombi"),
        help_text=_(
            "This allows you to subscribe to a Trombi. "
            "Be aware that you can subscribe only once, so don't play with that, "
            "or you will expose yourself to the admins' wrath!"
        ),
    )


class UserTrombiToolsView(
    LoginRequiredMixin, QuickNotifMixin, TrombiTabsMixin, TemplateView
):
    """Display a user's trombi tools."""

    template_name = "trombi/user_tools.jinja"
    current_tab = "tools"

    def post(self, request, *args, **kwargs):
        self.form = UserTrombiForm(request.POST)
        if self.form.is_valid():
            if hasattr(request.user, "trombi_user"):
                trombi_user = request.user.trombi_user
                trombi_user.trombi = self.form.cleaned_data["trombi"]
            else:
                trombi_user = TrombiUser(
                    user=request.user, trombi=self.form.cleaned_data["trombi"]
                )
            trombi_user.save()
            self.quick_notif_list += ["qn_success"]
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["user"] = self.request.user
        if not (
            hasattr(self.request.user, "trombi_user")
            and self.request.user.trombi_user.trombi
        ):
            kwargs["subscribe_form"] = UserTrombiForm()
        else:
            kwargs["trombi"] = self.request.user.trombi_user.trombi
            kwargs["date"] = date
        return kwargs


class UserTrombiEditPicturesView(TrombiTabsMixin, UserIsInATrombiMixin, UpdateView):
    model = TrombiUser
    fields = ["profile_pict", "scrub_pict"]
    template_name = "core/edit.jinja"
    current_tab = "pictures"

    def get_object(self):
        return self.request.user.trombi_user

    def get_success_url(self):
        return reverse("trombi:user_tools") + "?qn_success"


class UserTrombiEditProfileView(
    QuickNotifMixin, TrombiTabsMixin, UserIsInATrombiMixin, UpdateView
):
    model = User
    form_class = modelform_factory(
        User,
        fields=[
            "second_email",
            "phone",
            "department",
            "dpt_option",
            "quote",
            "parent_address",
        ],
        labels={
            "second_email": _("Personal email (not UTBM)"),
            "phone": _("Phone"),
            "parent_address": _("Native town"),
        },
    )
    template_name = "trombi/edit_profile.jinja"
    current_tab = "profile"

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse("trombi:user_tools") + "?qn_success"


class UserTrombiResetClubMembershipsView(UserIsInATrombiMixin, RedirectView):
    permanent = False

    def get(self, request, *args, **kwargs):
        user = self.request.user.trombi_user
        user.make_memberships()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("trombi:profile") + "?qn_success"


class UserTrombiDeleteMembershipView(TrombiTabsMixin, CanEditMixin, DeleteView):
    model = TrombiClubMembership
    pk_url_kwarg = "membership_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("trombi:profile")
    current_tab = "profile"

    def get_success_url(self):
        return super().get_success_url() + "?qn_success"


# Used by admins when someone does not have every club in his list
class UserTrombiAddMembershipView(TrombiTabsMixin, CreateView):
    model = TrombiClubMembership
    template_name = "core/edit.jinja"
    fields = ["club", "role", "start", "end"]
    pk_url_kwarg = "user_id"
    current_tab = "profile"

    def dispatch(self, request, *arg, **kwargs):
        self.trombi_user = get_object_or_404(TrombiUser, pk=kwargs["user_id"])
        if not self.trombi_user.trombi.is_owned_by(request.user):
            raise PermissionDenied()

        return super().dispatch(request, *arg, **kwargs)

    def form_valid(self, form):
        membership = form.save(commit=False)
        membership.user = self.trombi_user
        membership.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "trombi:detail", kwargs={"trombi_id": self.trombi_user.trombi.id}
        )


class UserTrombiEditMembershipView(CanEditMixin, TrombiTabsMixin, UpdateView):
    model = TrombiClubMembership
    pk_url_kwarg = "membership_id"
    fields = ["role", "start", "end"]
    template_name = "core/edit.jinja"
    current_tab = "profile"

    def get_success_url(self):
        return super().get_success_url() + "?qn_success"


class UserTrombiProfileView(TrombiTabsMixin, DetailView):
    model = TrombiUser
    pk_url_kwarg = "user_id"
    template_name = "trombi/user_profile.jinja"
    context_object_name = "trombi_user"
    current_tab = "tools"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.user.is_anonymous:
            raise PermissionDenied()

        if (
            self.object.trombi.id != request.user.trombi_user.trombi.id
            or self.object.user.id == request.user.id
            or not self.object.trombi.show_profiles
        ):
            raise Http404()
        return super().get(request, *args, **kwargs)


class TrombiCommentFormView(LoginRequiredMixin, View):
    """Create/edit a trombi comment."""

    model = TrombiComment
    fields = ["content"]
    template_name = "trombi/comment.jinja"

    def get_form_class(self):
        self.trombi = self.request.user.trombi_user.trombi
        if date.today() <= self.trombi.subscription_deadline:
            raise Http404(
                _(
                    "You can not yet write comment, you must wait for "
                    "the subscription deadline to be passed."
                )
            )
        if self.trombi.comments_deadline < date.today():
            raise Http404(
                _(
                    "You can not write comment anymore, the deadline is "
                    "already passed."
                )
            )
        return modelform_factory(
            self.model,
            fields=self.fields,
            widgets={
                "content": forms.widgets.Textarea(
                    attrs={"maxlength": self.trombi.max_chars}
                )
            },
            help_texts={
                "content": _("Maximum characters: %(max_length)s")
                % {"max_length": self.trombi.max_chars}
            },
        )

    def get_success_url(self):
        return reverse("trombi:user_tools") + "?qn_success"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if "user_id" in self.kwargs.keys():
            kwargs["target"] = get_object_or_404(TrombiUser, id=self.kwargs["user_id"])
        else:
            kwargs["target"] = self.object.target
        return kwargs


class TrombiCommentCreateView(TrombiCommentFormView, CreateView):
    def form_valid(self, form):
        target = get_object_or_404(TrombiUser, id=self.kwargs["user_id"])
        author = self.request.user.trombi_user
        form.instance.author = author
        form.instance.target = target
        # Check that this combination does not already have a comment
        old = TrombiComment.objects.filter(author=author, target=target).first()
        if old:
            old.content = form.instance.content
            old.save()
            return HttpResponseRedirect(self.get_success_url())
        return super().form_valid(form)


class TrombiCommentEditView(TrombiCommentFormView, CanViewMixin, UpdateView):
    pk_url_kwarg = "comment_id"

    def form_valid(self, form):
        form.instance.is_moderated = False
        return super().form_valid(form)
