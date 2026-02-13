#
# Copyright 2019
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

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    TemplateView,
    UpdateView,
)

from core.auth.mixins import PermissionOrAuthorRequiredMixin
from core.models import Notification, User
from core.views import DetailFormView
from pedagogy.forms import (
    UECommentForm,
    UECommentModerationForm,
    UECommentReportForm,
    UEForm,
)
from pedagogy.models import UE, UEComment, UECommentReport


class UEDetailFormView(PermissionRequiredMixin, DetailFormView):
    """Display every comment of an UE and detailed infos about it.

    Allow to comment the UE.
    """

    model = UE
    pk_url_kwarg = "ue_id"
    template_name = "pedagogy/ue_detail.jinja"
    form_class = UECommentForm
    permission_required = "pedagogy.view_ue"

    def has_permission(self):
        if self.request.method == "POST" and not self.request.user.has_perm(
            "pedagogy.add_uecomment"
        ):
            # if it's a POST request, the user is trying to add a new UEComment
            # thus he also needs the "add_uecomment" permission
            return False
        return super().has_permission()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["author_id"] = self.request.user.id
        kwargs["ue_id"] = self.object.id
        kwargs["is_creation"] = True
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "comments": list(
                self.object.comments.viewable_by(self.request.user)
                .annotate_is_reported()
                .select_related("author")
                .order_by("-publish_date")
            )
        }

    def get_success_url(self):
        # once the new ue comment has been saved
        # redirect to the same page we are currently
        return self.request.path


class UECommentUpdateView(PermissionOrAuthorRequiredMixin, UpdateView):
    """Allow edit of a given comment."""

    model = UEComment
    form_class = UECommentForm
    pk_url_kwarg = "comment_id"
    template_name = "core/edit.jinja"
    permission_required = "pedagogy.change_uecomment"
    author_field = "author"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["author_id"] = self.object.author_id
        kwargs["ue_id"] = self.object.ue_id
        kwargs["is_creation"] = False
        return kwargs

    def get_success_url(self):
        return reverse("pedagogy:ue_detail", kwargs={"ue_id": self.object.ue_id})


class UECommentDeleteView(PermissionOrAuthorRequiredMixin, DeleteView):
    """Allow to delete a given comment."""

    model = UEComment
    pk_url_kwarg = "comment_id"
    template_name = "core/delete_confirm.jinja"
    permission_required = "pedagogy.delete_uecomment"
    author_field = "author"

    def get_success_url(self):
        return reverse("pedagogy:ue_detail", kwargs={"ue_id": self.object.ue_id})


class UEGuideView(PermissionRequiredMixin, TemplateView):
    """UE guide main page."""

    template_name = "pedagogy/guide.jinja"
    permission_required = "pedagogy.view_ue"


class UECommentReportCreateView(PermissionRequiredMixin, CreateView):
    """Create a new report for an inappropriate comment."""

    model = UECommentReport
    form_class = UECommentReportForm
    template_name = "core/edit.jinja"
    permission_required = "pedagogy.add_uecommentreport"

    def dispatch(self, request, *args, **kwargs):
        self.ue_comment = get_object_or_404(UEComment, pk=kwargs["comment_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["reporter_id"] = self.request.user.id
        kwargs["comment_id"] = self.ue_comment.id
        return kwargs

    def form_valid(self, form):
        resp = super().form_valid(form)
        # Send a message to moderation admins
        unread_notif_subquery = Notification.objects.filter(
            user=OuterRef("pk"), type="PEDAGOGY_MODERATION", viewed=False
        )
        for user in User.objects.filter(
            ~Exists(unread_notif_subquery),
            groups__id__in=[settings.SITH_GROUP_PEDAGOGY_ADMIN_ID],
        ):
            Notification.objects.create(
                user=user,
                url=reverse("pedagogy:moderation"),
                type="PEDAGOGY_MODERATION",
            )

        return resp

    def get_success_url(self):
        return reverse("pedagogy:ue_detail", kwargs={"ue_id": self.ue_comment.ue_id})


class UEModerationFormView(PermissionRequiredMixin, FormView):
    """Moderation interface (Privileged)."""

    form_class = UECommentModerationForm
    template_name = "pedagogy/moderation.jinja"
    permission_required = "pedagogy.delete_uecomment"
    success_url = reverse_lazy("pedagogy:moderation")

    def form_valid(self, form):
        form_clean = form.clean()
        accepted = form_clean.get("accepted_reports", [])
        if len(accepted) > 0:  # delete the reported comments
            UEComment.objects.filter(reports__in=accepted).delete()
        denied = form_clean.get("denied_reports", [])
        if len(denied) > 0:  # delete the comments themselves
            UECommentReport.objects.filter(id__in={d.id for d in denied}).delete()
        return super().form_valid(form)


class UECreateView(PermissionRequiredMixin, CreateView):
    """Add a new UE (Privileged)."""

    model = UE
    form_class = UEForm
    template_name = "pedagogy/ue_edit.jinja"
    permission_required = "pedagogy.add_ue"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["author_id"] = self.request.user.id
        return kwargs


class UEDeleteView(PermissionRequiredMixin, DeleteView):
    """Allow to delete an UE (Privileged)."""

    model = UE
    pk_url_kwarg = "ue_id"
    template_name = "core/delete_confirm.jinja"
    permission_required = "pedagogy.delete_ue"
    success_url = reverse_lazy("pedagogy:guide")


class UEUpdateView(PermissionRequiredMixin, UpdateView):
    """Allow to edit an UE (Privilegied)."""

    model = UE
    form_class = UEForm
    pk_url_kwarg = "ue_id"
    template_name = "pedagogy/ue_edit.jinja"
    permission_required = "pedagogy.change_ue"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        obj = self.get_object()
        kwargs["author_id"] = obj.author_id
        return kwargs
