# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import html
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
    View,
)
from haystack.query import SearchQuerySet
from rest_framework.renderers import JSONRenderer

from core.models import Notification, RealGroup
from core.views import (
    CanCreateMixin,
    CanEditPropMixin,
    CanViewMixin,
    DetailFormView,
)
from pedagogy.forms import (
    UVCommentForm,
    UVCommentModerationForm,
    UVCommentReportForm,
    UVForm,
)
from pedagogy.models import UV, UVComment, UVCommentReport, UVSerializer

# Some mixins


class CanCreateUVFunctionMixin(View):
    """
    Add the function can_create_uv(user) into the template
    """

    @staticmethod
    def can_create_uv(user):
        """
        Creates a dummy instance of UV and test is_owner
        """
        return user.is_owner(UV())

    def get_context_data(self, **kwargs):
        """
        Pass the function to the template
        """
        kwargs = super(CanCreateUVFunctionMixin, self).get_context_data(**kwargs)
        kwargs["can_create_uv"] = self.can_create_uv
        return kwargs


# Acutal views


class UVDetailFormView(CanViewMixin, CanCreateUVFunctionMixin, DetailFormView):
    """
    Dispaly every comment of an UV and detailed infos about it
    Allow to comment the UV
    """

    model = UV
    pk_url_kwarg = "uv_id"
    template_name = "pedagogy/uv_detail.jinja"
    form_class = UVCommentForm

    def get_form_kwargs(self):
        kwargs = super(UVDetailFormView, self).get_form_kwargs()
        kwargs["author_id"] = self.request.user.id
        kwargs["uv_id"] = self.get_object().id
        kwargs["is_creation"] = True
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(UVDetailFormView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "pedagogy:uv_detail", kwargs={"uv_id": self.get_object().id}
        )


class UVCommentUpdateView(CanEditPropMixin, UpdateView):
    """
    Allow edit of a given comment
    """

    model = UVComment
    form_class = UVCommentForm
    pk_url_kwarg = "comment_id"
    template_name = "core/edit.jinja"

    def get_form_kwargs(self):
        kwargs = super(UVCommentUpdateView, self).get_form_kwargs()
        obj = self.get_object()
        kwargs["author_id"] = obj.author.id
        kwargs["uv_id"] = obj.uv.id
        kwargs["is_creation"] = False

        return kwargs

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.uv.id})


class UVCommentDeleteView(CanEditPropMixin, DeleteView):
    """
    Allow delete of a given comment
    """

    model = UVComment
    pk_url_kwarg = "comment_id"
    template_name = "core/delete_confirm.jinja"

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.uv.id})


class UVListView(CanViewMixin, CanCreateUVFunctionMixin, ListView):
    """
    UV guide main page
    """

    # This is very basic and is prone to changment

    model = UV
    ordering = ["code"]
    template_name = "pedagogy/guide.jinja"

    def get(self, *args, **kwargs):
        if not self.request.GET.get("json", None):
            # Return normal full template response
            return super(UVListView, self).get(*args, **kwargs)

        # Return serialized response
        return HttpResponse(
            JSONRenderer().render(UVSerializer(self.get_queryset(), many=True).data),
            content_type="application/json",
        )

    def get_queryset(self):
        queryset = super(UVListView, self).get_queryset()
        search = self.request.GET.get("search", None)

        additional_filters = {}

        for filter_type in ["credit_type", "language", "department"]:
            arg = self.request.GET.get(filter_type, None)
            if arg:
                additional_filters[filter_type] = arg

        semester = self.request.GET.get("semester", None)
        if semester:
            if semester in ["AUTUMN", "SPRING"]:
                additional_filters["semester__in"] = [semester, "AUTUMN_AND_SPRING"]
            else:
                additional_filters["semester"] = semester

        queryset = queryset.filter(**additional_filters)
        if not search:
            return queryset

        if len(search) == 1:
            # It's a search with only one letter
            # Haystack doesn't work well with only one letter
            return queryset.filter(code__istartswith=search)

        try:
            qs = (
                SearchQuerySet()
                .models(self.model)
                .autocomplete(auto=html.escape(search))
            )
        except TypeError:
            return self.model.objects.none()

        return queryset.filter(
            id__in=([o.object.id for o in qs if o.object is not None])
        )


class UVCommentReportCreateView(CanCreateMixin, CreateView):
    """
    Create a new report for an inapropriate comment
    """

    model = UVCommentReport
    form_class = UVCommentReportForm
    template_name = "core/edit.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.uv_comment = get_object_or_404(UVComment, pk=kwargs["comment_id"])
        return super(UVCommentReportCreateView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(UVCommentReportCreateView, self).get_form_kwargs()
        kwargs["reporter_id"] = self.request.user.id
        kwargs["comment_id"] = self.uv_comment.id
        return kwargs

    def form_valid(self, form):
        resp = super(UVCommentReportCreateView, self).form_valid(form)

        # Send a message to moderation admins
        for user in (
            RealGroup.objects.filter(id=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)
            .first()
            .users.all()
        ):
            if not user.notifications.filter(
                type="PEDAGOGY_MODERATION", viewed=False
            ).exists():
                Notification(
                    user=user,
                    url=reverse("pedagogy:moderation"),
                    type="PEDAGOGY_MODERATION",
                ).save()

        return resp

    def get_success_url(self):
        return reverse_lazy(
            "pedagogy:uv_detail", kwargs={"uv_id": self.uv_comment.uv.id}
        )


class UVModerationFormView(FormView):
    """
    Moderation interface (Privileged)
    """

    form_class = UVCommentModerationForm
    template_name = "pedagogy/moderation.jinja"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_owner(UV()):
            raise PermissionDenied
        return super(UVModerationFormView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form_clean = form.clean()
        for report in form_clean.get("accepted_reports", []):
            try:
                report.comment.delete()  # Delete the related comment
            except ObjectDoesNotExist:
                # To avoid errors when two reports points the same comment
                pass
        for report in form_clean.get("denied_reports", []):
            try:
                report.delete()  # Delete the report itself
            except ObjectDoesNotExist:
                # To avoid errors when two reports points the same comment
                pass
        return super(UVModerationFormView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy("pedagogy:moderation")


class UVCreateView(CanCreateMixin, CreateView):
    """
    Add a new UV (Privileged)
    """

    model = UV
    form_class = UVForm
    template_name = "pedagogy/uv_edit.jinja"

    def get_form_kwargs(self):
        kwargs = super(UVCreateView, self).get_form_kwargs()
        kwargs["author_id"] = self.request.user.id
        return kwargs

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.id})


class UVDeleteView(CanEditPropMixin, DeleteView):
    """
    Allow to delete an UV (Privileged)
    """

    model = UV
    pk_url_kwarg = "uv_id"
    template_name = "core/delete_confirm.jinja"

    def get_success_url(self):
        return reverse_lazy("pedagogy:guide")


class UVUpdateView(CanEditPropMixin, UpdateView):
    """
    Allow to edit an UV (Privilegied)
    """

    model = UV
    form_class = UVForm
    pk_url_kwarg = "uv_id"
    template_name = "pedagogy/uv_edit.jinja"

    def get_form_kwargs(self):
        kwargs = super(UVUpdateView, self).get_form_kwargs()
        obj = self.get_object()
        kwargs["author_id"] = obj.author.id
        return kwargs

    def get_success_url(self):
        return reverse_lazy("pedagogy:uv_detail", kwargs={"uv_id": self.object.id})
