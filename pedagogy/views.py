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
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
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

from core.auth.mixins import CanEditPropMixin, CanViewMixin, FormerSubscriberMixin
from core.models import Notification, User
from core.views import DetailFormView
from pedagogy.forms import (
    UVCommentForm,
    UVCommentModerationForm,
    UVCommentReportForm,
    UVForm,
)
from pedagogy.models import UV, UVComment, UVCommentReport


class UVDetailFormView(CanViewMixin, DetailFormView):
    """Display every comment of an UV and detailed infos about it.

    Allow to comment the UV.
    """

    model = UV
    pk_url_kwarg = "uv_id"
    template_name = "pedagogy/uv_detail.jinja"
    form_class = UVCommentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["author_id"] = self.request.user.id
        kwargs["uv_id"] = self.get_object().id
        kwargs["is_creation"] = True
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "pedagogy:uv_detail", kwargs={"uv_id": self.get_object().id}
        )

    def get_context_data(self, **kwargs):
        user = self.request.user
        return super().get_context_data(**kwargs) | {
            "can_create_uv": (
                user.is_root
                or user.is_in_group(pk=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)
            )
        }


class UVCommentUpdateView(CanEditPropMixin, UpdateView):
    """Allow edit of a given comment."""

    model = UVComment
    form_class = UVCommentForm
    pk_url_kwarg = "comment_id"
    template_name = "core/edit.jinja"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        obj = self.get_object()
        kwargs["author_id"] = obj.author.id
        kwargs["uv_id"] = obj.uv.id
        kwargs["is_creation"] = False

        return kwargs

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.uv.id})


class UVCommentDeleteView(CanEditPropMixin, DeleteView):
    """Allow delete of a given comment."""

    model = UVComment
    pk_url_kwarg = "comment_id"
    template_name = "core/delete_confirm.jinja"

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.uv.id})


class UVGuideView(LoginRequiredMixin, FormerSubscriberMixin, TemplateView):
    """UV guide main page."""

    template_name = "pedagogy/guide.jinja"

    def get_context_data(self, **kwargs):
        user = self.request.user
        return super().get_context_data(**kwargs) | {
            "can_create_uv": (
                user.is_root
                or user.is_in_group(pk=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)
            )
        }


class UVCommentReportCreateView(PermissionRequiredMixin, CreateView):
    """Create a new report for an inapropriate comment."""

    model = UVCommentReport
    form_class = UVCommentReportForm
    template_name = "core/edit.jinja"
    permission_required = "pedagogy.add_uvcommentreport"

    def dispatch(self, request, *args, **kwargs):
        self.uv_comment = get_object_or_404(UVComment, pk=kwargs["comment_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["reporter_id"] = self.request.user.id
        kwargs["comment_id"] = self.uv_comment.id
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
        return reverse_lazy(
            "pedagogy:uv_detail", kwargs={"uv_id": self.uv_comment.uv.id}
        )


class UVModerationFormView(FormView):
    """Moderation interface (Privileged)."""

    form_class = UVCommentModerationForm
    template_name = "pedagogy/moderation.jinja"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_owner(UV()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form_clean = form.clean()
        accepted = form_clean.get("accepted_reports", [])
        if len(accepted) > 0:  # delete the reported comments
            UVComment.objects.filter(reports__in=accepted).delete()
        denied = form_clean.get("denied_reports", [])
        if len(denied) > 0:  # delete the comments themselves
            UVCommentReport.objects.filter(id__in={d.id for d in denied}).delete()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("pedagogy:moderation")


class UVCreateView(PermissionRequiredMixin, CreateView):
    """Add a new UV (Privileged)."""

    model = UV
    form_class = UVForm
    template_name = "pedagogy/uv_edit.jinja"
    permission_required = "pedagogy.add_uv"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["author_id"] = self.request.user.id
        return kwargs

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.id})


class UVDeleteView(CanEditPropMixin, DeleteView):
    """Allow to delete an UV (Privileged)."""

    model = UV
    pk_url_kwarg = "uv_id"
    template_name = "core/delete_confirm.jinja"

    def get_success_url(self):
        return reverse_lazy("pedagogy:guide")


class UVUpdateView(CanEditPropMixin, UpdateView):
    """Allow to edit an UV (Privilegied)."""

    model = UV
    form_class = UVForm
    pk_url_kwarg = "uv_id"
    template_name = "pedagogy/uv_edit.jinja"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        obj = self.get_object()
        kwargs["author_id"] = obj.author.id
        return kwargs

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.id})
