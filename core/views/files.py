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

# This file contains all the views that concern the page model
import os
from wsgiref.util import FileWrapper

from ajax_select import make_ajax_field
from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import http_date
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeleteView, FormMixin, UpdateView

from core.models import Notification, RealGroup, SithFile
from core.views import (
    CanEditMixin,
    CanEditPropMixin,
    CanViewMixin,
    can_view,
)
from counter.models import Counter


def send_file(request, file_id, file_class=SithFile, file_attr="file"):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    f = get_object_or_404(file_class, id=file_id)
    if not (
        can_view(f, request.user)
        or (
            "counter_token" in request.session.keys()
            and request.session["counter_token"]
            and Counter.objects.filter(  # check if not null for counters that have no token set
                token=request.session["counter_token"]
            ).exists()
        )
    ):
        raise PermissionDenied
    name = f.__getattribute__(file_attr).name
    filepath = os.path.join(settings.MEDIA_ROOT, name)

    # check if file exists on disk
    if not os.path.exists(filepath.encode("utf-8")):
        raise Http404()

    with open(filepath.encode("utf-8"), "rb") as filename:
        wrapper = FileWrapper(filename)
        response = HttpResponse(wrapper, content_type=f.mime_type)
        response["Last-Modified"] = http_date(f.date.timestamp())
        response["Content-Length"] = os.path.getsize(filepath.encode("utf-8"))
        response["Content-Disposition"] = ('inline; filename="%s"' % f.name).encode(
            "utf-8"
        )
        return response


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class _MultipleFieldMixin:
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class MultipleFileField(_MultipleFieldMixin, forms.FileField): ...


class MultipleImageField(_MultipleFieldMixin, forms.ImageField): ...


class AddFilesForm(forms.Form):
    folder_name = forms.CharField(
        label=_("Add a new folder"), max_length=30, required=False
    )
    file_field = MultipleFileField(
        label=_("Files"),
        required=False,
    )

    def process(self, parent, owner, files):
        notif = False
        try:
            if self.cleaned_data["folder_name"] != "":
                folder = SithFile(
                    parent=parent, name=self.cleaned_data["folder_name"], owner=owner
                )
                folder.clean()
                folder.save()
                notif = True
        except Exception as e:
            self.add_error(
                None,
                _("Error creating folder %(folder_name)s: %(msg)s")
                % {"folder_name": self.cleaned_data["folder_name"], "msg": repr(e)},
            )
        for f in files:
            new_file = SithFile(
                parent=parent,
                name=f.name,
                file=f,
                owner=owner,
                is_folder=False,
                mime_type=f.content_type,
                size=f.size,
            )
            try:
                new_file.clean()
                new_file.save()
                notif = True
            except Exception as e:
                self.add_error(
                    None,
                    _("Error uploading file %(file_name)s: %(msg)s")
                    % {"file_name": f, "msg": repr(e)},
                )
        if notif:
            for u in (
                RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID)
                .first()
                .users.all()
            ):
                if not u.notifications.filter(
                    type="FILE_MODERATION", viewed=False
                ).exists():
                    Notification(
                        user=u,
                        url=reverse("core:file_moderation"),
                        type="FILE_MODERATION",
                    ).save()


class FileListView(ListView):
    template_name = "core/file_list.jinja"
    context_object_name = "file_list"

    def get_queryset(self):
        return SithFile.objects.filter(parent=None)

    def get_context_data(self, **kwargs):
        kwargs = super(FileListView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        return kwargs


class FileEditView(CanEditMixin, UpdateView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_edit.jinja"
    context_object_name = "file"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_be_managed_by(request.user):
            raise PermissionDenied

        return super(FileEditView, self).get(request, *args, **kwargs)

    def get_form_class(self):
        fields = ["name", "is_moderated"]
        if self.object.is_file:
            fields = ["file"] + fields
        return modelform_factory(SithFile, fields=fields)

    def get_success_url(self):
        if self.kwargs.get("popup") is not None:
            return reverse(
                "core:file_detail", kwargs={"file_id": self.object.id, "popup": "popup"}
            )
        return reverse(
            "core:file_detail", kwargs={"file_id": self.object.id, "popup": ""}
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileEditView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        return kwargs


class FileEditPropForm(forms.ModelForm):
    class Meta:
        model = SithFile
        fields = ["parent", "owner", "edit_groups", "view_groups"]

    parent = make_ajax_field(SithFile, "parent", "files", help_text="")
    edit_groups = make_ajax_field(
        SithFile, "edit_groups", "groups", help_text="", label=_("edit group")
    )
    view_groups = make_ajax_field(
        SithFile, "view_groups", "groups", help_text="", label=_("view group")
    )
    recursive = forms.BooleanField(label=_("Apply rights recursively"), required=False)


class FileEditPropView(CanEditPropMixin, UpdateView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_edit.jinja"
    context_object_name = "file"
    form_class = FileEditPropForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_be_managed_by(request.user):
            raise PermissionDenied

        return super(FileEditPropView, self).get(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super(FileEditPropView, self).get_form(form_class)
        form.fields["parent"].queryset = SithFile.objects.filter(is_folder=True)
        return form

    def form_valid(self, form):
        ret = super(FileEditPropView, self).form_valid(form)
        if form.cleaned_data["recursive"]:
            self.object.apply_rights_recursively()
        return ret

    def get_success_url(self):
        return reverse(
            "core:file_detail",
            kwargs={"file_id": self.object.id, "popup": self.kwargs.get("popup", "")},
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileEditPropView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        return kwargs


class FileView(CanViewMixin, DetailView, FormMixin):
    """This class handle the upload of new files into a folder"""

    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_detail.jinja"
    context_object_name = "file"
    form_class = AddFilesForm

    def handle_clipboard(request, object):
        """
        This method handles the clipboard in the view.
        This method can fail, since it does not catch the exceptions coming from
        below, allowing proper handling in the calling view.
        Use this method like this:

            FileView.handle_clipboard(request, self.object)

        `request` is usually the self.request object in your view
        `object` is the SithFile object you want to put in the clipboard, or
                 where you want to paste the clipboard
        """
        if "delete" in request.POST.keys():
            for f_id in request.POST.getlist("file_list"):
                sf = SithFile.objects.filter(id=f_id).first()
                if sf:
                    sf.delete()
        if "clear" in request.POST.keys():
            request.session["clipboard"] = []
        if "cut" in request.POST.keys():
            for f_id in request.POST.getlist("file_list"):
                f_id = int(f_id)
                if (
                    f_id in [c.id for c in object.children.all()]
                    and f_id not in request.session["clipboard"]
                ):
                    request.session["clipboard"].append(f_id)
        if "paste" in request.POST.keys():
            for f_id in request.session["clipboard"]:
                sf = SithFile.objects.filter(id=f_id).first()
                if sf:
                    sf.move_to(object)
            request.session["clipboard"] = []
        request.session.modified = True

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if not self.object.can_be_managed_by(request.user):
            raise PermissionDenied

        if "clipboard" not in request.session.keys():
            request.session["clipboard"] = []
        return super(FileView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "clipboard" not in request.session.keys():
            request.session["clipboard"] = []
        if request.user.can_edit(self.object):
            # XXX this call can fail!
            FileView.handle_clipboard(request, self.object)
        self.form = self.get_form()  # The form handle only the file upload
        files = request.FILES.getlist("file_field")
        if (
            request.user.is_authenticated
            and request.user.can_edit(self.object)
            and self.form.is_valid()
        ):
            self.form.process(parent=self.object, owner=request.user, files=files)
            if self.form.is_valid():
                return super(FileView, self).form_valid(self.form)
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse(
            "core:file_detail",
            kwargs={"file_id": self.object.id, "popup": self.kwargs.get("popup", "")},
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        kwargs["form"] = self.form
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        kwargs["clipboard"] = SithFile.objects.filter(
            id__in=self.request.session["clipboard"]
        )
        return kwargs


class FileDeleteView(CanEditPropMixin, DeleteView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_delete_confirm.jinja"
    context_object_name = "file"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_be_managed_by(request.user):
            raise PermissionDenied

        return super(FileDeleteView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        self.object.file.delete()  # Doing it here or overloading delete() is the same, so let's do it here
        if "next" in self.request.GET.keys():
            return self.request.GET["next"]
        if self.object.parent is None:
            return reverse(
                "core:file_list", kwargs={"popup": self.kwargs.get("popup", "")}
            )
        return reverse(
            "core:file_detail",
            kwargs={
                "file_id": self.object.parent.id,
                "popup": self.kwargs.get("popup", ""),
            },
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileDeleteView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        return kwargs


class FileModerationView(TemplateView):
    template_name = "core/file_moderation.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(FileModerationView, self).get_context_data(**kwargs)
        kwargs["files"] = SithFile.objects.filter(is_moderated=False)[:100]
        return kwargs


class FileModerateView(CanEditPropMixin, SingleObjectMixin):
    model = SithFile
    pk_url_kwarg = "file_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_moderated = True
        self.object.moderator = request.user
        self.object.save()
        if "next" in self.request.GET.keys():
            return redirect(self.request.GET["next"])
        return redirect("core:file_moderation")
