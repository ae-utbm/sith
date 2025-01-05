#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
import mimetypes
from pathlib import Path
from urllib.parse import quote, urljoin

# This file contains all the views that concern the page model
from wsgiref.util import FileWrapper

from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef
from django.forms.models import modelform_factory
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import http_date
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeleteView, FormMixin, UpdateView

from core.models import Notification, SithFile, User
from core.views import (
    AllowFragment,
    CanEditMixin,
    CanEditPropMixin,
    CanViewMixin,
    can_view,
)
from core.views.widgets.select import (
    AutoCompleteSelectMultipleGroup,
    AutoCompleteSelectSithFile,
    AutoCompleteSelectUser,
)
from counter.utils import is_logged_in_counter


def send_raw_file(path: Path) -> HttpResponse:
    """Send a file located in the MEDIA_ROOT

    This handles all the logic of using production reverse proxy or debug server.

    THIS DOESN'T CHECK ANY PERMISSIONS !
    """
    if not path.is_relative_to(settings.MEDIA_ROOT):
        raise Http404

    if not path.is_file() or not path.exists():
        raise Http404

    response = HttpResponse(
        headers={"Content-Disposition": f'inline; filename="{quote(path.name)}"'}
    )
    if not settings.DEBUG:
        # When receiving a response with the Accel-Redirect header,
        # the reverse proxy will automatically handle the file sending.
        # This is really hard to test (thus isn't tested)
        # so please do not mess with this.
        response["Content-Type"] = ""  # automatically set by nginx
        response["X-Accel-Redirect"] = quote(
            urljoin(settings.MEDIA_URL, str(path.relative_to(settings.MEDIA_ROOT)))
        )
        return response

    with open(path, "rb") as filename:
        response.content = FileWrapper(filename)
        response["Content-Type"] = mimetypes.guess_type(path)[0]
        response["Last-Modified"] = http_date(path.stat().st_mtime)
        response["Content-Length"] = path.stat().st_size
        return response


def send_file(
    request: HttpRequest,
    file_id: int,
    file_class: type[SithFile] = SithFile,
    file_attr: str = "file",
) -> HttpResponse:
    """Send a protected file, if the user can see it.

    In prod, the server won't handle the download itself,
    but set the appropriate headers in the response to make the reverse-proxy
    deal with it.
    In debug mode, the server will directly send the file.
    """
    f = get_object_or_404(file_class, id=file_id)
    if not can_view(f, request.user) and not is_logged_in_counter(request):
        raise PermissionDenied
    name = getattr(f, file_attr).name

    return send_raw_file(settings.MEDIA_ROOT / name)


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
            unread_notif_subquery = Notification.objects.filter(
                user=OuterRef("pk"), type="FILE_MODERATION", viewed=False
            )
            for user in User.objects.filter(
                ~Exists(unread_notif_subquery),
                groups__id__in=[settings.SITH_GROUP_COM_ADMIN_ID],
            ):
                Notification.objects.create(
                    user=user,
                    url=reverse("core:file_moderation"),
                    type="FILE_MODERATION",
                )


class FileListView(ListView):
    template_name = "core/file_list.jinja"
    context_object_name = "file_list"

    def get_queryset(self):
        return SithFile.objects.filter(parent=None)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
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
            fields = ["file", *fields]
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
        kwargs = super().get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        return kwargs


class FileEditPropForm(forms.ModelForm):
    class Meta:
        model = SithFile
        fields = ["parent", "owner", "edit_groups", "view_groups"]
        widgets = {
            "parent": AutoCompleteSelectSithFile,
            "owner": AutoCompleteSelectUser,
            "edit_groups": AutoCompleteSelectMultipleGroup,
            "view_groups": AutoCompleteSelectMultipleGroup,
        }

    recursive = forms.BooleanField(label=_("Apply rights recursively"), required=False)


class FileEditPropView(CanEditPropMixin, UpdateView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_edit.jinja"
    context_object_name = "file"
    form_class = FileEditPropForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["parent"].queryset = SithFile.objects.filter(is_folder=True)
        return form

    def form_valid(self, form):
        ret = super().form_valid(form)
        if form.cleaned_data["recursive"]:
            self.object.apply_rights_recursively()
        return ret

    def get_success_url(self):
        return reverse(
            "core:file_detail",
            kwargs={"file_id": self.object.id, "popup": self.kwargs.get("popup", "")},
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["popup"] = ""
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        return kwargs


class FileView(CanViewMixin, DetailView, FormMixin):
    """Handle the upload of new files into a folder."""

    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_detail.jinja"
    context_object_name = "file"
    form_class = AddFilesForm

    @staticmethod
    def handle_clipboard(request, obj):
        """Handle the clipboard in the view.

        This method can fail, since it does not catch the exceptions coming from
        below, allowing proper handling in the calling view.
        Use this method like this:

            FileView.handle_clipboard(request, self.object)

        `request` is usually the self.request obj in your view
        `obj` is the SithFile object you want to put in the clipboard, or
                 where you want to paste the clipboard
        """
        if "delete" in request.POST:
            for f_id in request.POST.getlist("file_list"):
                file = SithFile.objects.filter(id=f_id).first()
                if file:
                    file.delete()
        if "clear" in request.POST:
            request.session["clipboard"] = []
        if "cut" in request.POST:
            for f_id_str in request.POST.getlist("file_list"):
                f_id = int(f_id_str)
                if (
                    f_id in [c.id for c in obj.children.all()]
                    and f_id not in request.session["clipboard"]
                ):
                    request.session["clipboard"].append(f_id)
        if "paste" in request.POST:
            for f_id in request.session["clipboard"]:
                file = SithFile.objects.filter(id=f_id).first()
                if file:
                    file.move_to(obj)
            request.session["clipboard"] = []
        request.session.modified = True

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if "clipboard" not in request.session:
            request.session["clipboard"] = []
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "clipboard" not in request.session:
            request.session["clipboard"] = []
        if request.user.can_edit(self.object):
            # XXX this call can fail!
            self.handle_clipboard(request, self.object)
        self.form = self.get_form()  # The form handle only the file upload
        files = request.FILES.getlist("file_field")
        if (
            request.user.is_authenticated
            and request.user.can_edit(self.object)
            and self.form.is_valid()
        ):
            self.form.process(parent=self.object, owner=request.user, files=files)
            if self.form.is_valid():
                return super().form_valid(self.form)
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse(
            "core:file_detail",
            kwargs={"file_id": self.object.id, "popup": self.kwargs.get("popup", "")},
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["popup"] = ""
        kwargs["form"] = self.form
        if self.kwargs.get("popup") is not None:
            kwargs["popup"] = "popup"
        kwargs["clipboard"] = SithFile.objects.filter(
            id__in=self.request.session["clipboard"]
        )
        return kwargs


class FileDeleteView(AllowFragment, CanEditPropMixin, DeleteView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = "core/file_delete_confirm.jinja"
    context_object_name = "file"

    def get_success_url(self):
        self.object.file.delete()  # Doing it here or overloading delete() is the same, so let's do it here
        if "next" in self.request.GET:
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
        kwargs = super().get_context_data(**kwargs)
        kwargs["popup"] = "" if self.kwargs.get("popup") is None else "popup"
        kwargs["next"] = self.request.GET.get("next", None)
        kwargs["previous"] = self.request.GET.get("previous", None)
        kwargs["current"] = self.request.path
        return kwargs


class FileModerationView(AllowFragment, ListView):
    model = SithFile
    template_name = "core/file_moderation.jinja"
    queryset = SithFile.objects.filter(is_moderated=False, is_in_sas=False)
    paginate_by = 100

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        user: User = request.user
        if user.is_root:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class FileModerateView(CanEditPropMixin, SingleObjectMixin):
    model = SithFile
    pk_url_kwarg = "file_id"

    # FIXME : wrong http method. This should be a POST or a DELETE request
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_moderated = True
        self.object.moderator = request.user
        self.object.save()
        if "next" in self.request.GET:
            return redirect(self.request.GET["next"])
        return redirect("core:file_moderation")
