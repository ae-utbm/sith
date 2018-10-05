# -*- coding:utf-8 -*
#
# Copyright 2016,2017
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

# This file contains all the views that concern the page model
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import UpdateView, FormMixin, DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.forms.models import modelform_factory
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django import forms

import os

from ajax_select import make_ajax_field

from core.models import SithFile, RealGroup, Notification
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, can_view, not_found
from counter.models import Counter


def send_file(request, file_id, file_class=SithFile, file_attr="file"):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    f = file_class.objects.filter(id=file_id).first()
    if f is None or not f.file:
        return not_found(request)
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
    with open(filepath.encode("utf-8"), "rb") as filename:
        wrapper = FileWrapper(filename)
        response = HttpResponse(wrapper, content_type=f.mime_type)
        response["Content-Length"] = os.path.getsize(filepath.encode("utf-8"))
        response["Content-Disposition"] = ('inline; filename="%s"' % f.name).encode(
            "utf-8"
        )
        return response


class AddFilesForm(forms.Form):
    folder_name = forms.CharField(
        label=_("Add a new folder"), max_length=30, required=False
    )
    file_field = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
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
                size=f._size,
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
        if self.kwargs["popup"]:
            kwargs["popup"] = "popup"
        return kwargs


class FileEditView(CanEditMixin, UpdateView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_edit.jinja"
    context_object_name = "file"

    def get_form_class(self):
        fields = ["name", "is_moderated"]
        if self.object.is_file:
            fields = ["file"] + fields
        return modelform_factory(SithFile, fields=fields)

    def get_success_url(self):
        if self.kwargs["popup"]:
            return reverse(
                "core:file_detail", kwargs={"file_id": self.object.id, "popup": "popup"}
            )
        return reverse(
            "core:file_detail", kwargs={"file_id": self.object.id, "popup": ""}
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileEditView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs["popup"]:
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
            kwargs={"file_id": self.object.id, "popup": self.kwargs["popup"] or ""},
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileEditPropView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs["popup"]:
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
            request.user.is_authenticated()
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
            kwargs={"file_id": self.object.id, "popup": self.kwargs["popup"] or ""},
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        kwargs["form"] = self.form
        if self.kwargs["popup"]:
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

    def get_success_url(self):
        self.object.file.delete()  # Doing it here or overloading delete() is the same, so let's do it here
        if "next" in self.request.GET.keys():
            return self.request.GET["next"]
        if self.object.parent is None:
            return reverse(
                "core:file_list", kwargs={"popup": self.kwargs["popup"] or ""}
            )
        return reverse(
            "core:file_detail",
            kwargs={
                "file_id": self.object.parent.id,
                "popup": self.kwargs["popup"] or "",
            },
        )

    def get_context_data(self, **kwargs):
        kwargs = super(FileDeleteView, self).get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs["popup"]:
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
