#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectMultipleField
from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import FormMixin, FormView, UpdateView

from core.models import SithFile, User
from core.views import CanEditMixin, CanViewMixin
from core.views.files import FileView, MultipleImageField, send_file
from core.views.forms import SelectDate
from sas.models import Album, PeoplePictureRelation, Picture


class SASForm(forms.Form):
    album_name = forms.CharField(
        label=_("Add a new album"), max_length=Album.NAME_MAX_LENGTH, required=False
    )
    images = MultipleImageField(
        label=_("Upload images"),
        required=False,
    )

    def process(self, parent, owner, files, *, automodere=False):
        try:
            if self.cleaned_data["album_name"] != "":
                album = Album(
                    parent=parent,
                    name=self.cleaned_data["album_name"],
                    owner=owner,
                    is_moderated=automodere,
                )
                album.clean()
                album.save()
        except Exception as e:
            self.add_error(
                None,
                _("Error creating album %(album)s: %(msg)s")
                % {"album": self.cleaned_data["album_name"], "msg": repr(e)},
            )
        for f in files:
            new_file = Picture(
                parent=parent,
                name=f.name,
                file=f,
                owner=owner,
                mime_type=f.content_type,
                size=f.size,
                is_folder=False,
                is_moderated=automodere,
            )
            if automodere:
                new_file.moderator = owner
            try:
                new_file.clean()
                new_file.generate_thumbnails()
                new_file.save()
            except Exception as e:
                self.add_error(
                    None,
                    _("Error uploading file %(file_name)s: %(msg)s")
                    % {"file_name": f, "msg": repr(e)},
                )


class RelationForm(forms.ModelForm):
    class Meta:
        model = PeoplePictureRelation
        fields = ["picture"]
        widgets = {"picture": forms.HiddenInput}

    users = AutoCompleteSelectMultipleField(
        "users", show_help_text=False, help_text="", label=_("Add user"), required=False
    )


class SASMainView(FormView):
    form_class = SASForm
    template_name = "sas/main.jinja"
    success_url = reverse_lazy("sas:main")

    def post(self, request, *args, **kwargs):
        self.form = self.get_form()
        parent = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        files = request.FILES.getlist("images")
        root = User.objects.filter(username="root").first()
        if request.user.is_authenticated and request.user.is_in_group(
            pk=settings.SITH_GROUP_SAS_ADMIN_ID
        ):
            if self.form.is_valid():
                self.form.process(
                    parent=parent, owner=root, files=files, automodere=True
                )
                if self.form.is_valid():
                    return super().form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        albums_qs = Album.objects.viewable_by(self.request.user)
        kwargs["categories"] = list(
            albums_qs.filter(parent_id=settings.SITH_SAS_ROOT_DIR_ID).order_by("id")
        )
        kwargs["latest"] = list(albums_qs.order_by("-id")[:5])
        return kwargs


class PictureView(CanViewMixin, DetailView):
    model = Picture
    pk_url_kwarg = "picture_id"
    template_name = "sas/picture.jinja"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "rotate_right" in request.GET:
            self.object.rotate(270)
        if "rotate_left" in request.GET:
            self.object.rotate(90)
        if "ask_removal" in request.GET.keys():
            self.object.is_moderated = False
            self.object.asked_for_removal = True
            self.object.save()
            return redirect("sas:album", album_id=self.object.parent.id)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "album": Album.objects.get(children=self.object)
        }


def send_album(request, album_id):
    return send_file(request, album_id, Album)


def send_pict(request, picture_id):
    return send_file(request, picture_id, Picture)


def send_compressed(request, picture_id):
    return send_file(request, picture_id, Picture, "compressed")


def send_thumb(request, picture_id):
    return send_file(request, picture_id, Picture, "thumbnail")


class AlbumUploadView(CanViewMixin, DetailView, FormMixin):
    model = Album
    form_class = SASForm
    pk_url_kwarg = "album_id"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.file:
            self.object.generate_thumbnail()
        self.form = self.get_form()
        parent = SithFile.objects.filter(id=self.object.id).first()
        files = request.FILES.getlist("images")
        if request.user.is_authenticated and request.user.is_subscribed:
            if self.form.is_valid():
                self.form.process(
                    parent=parent,
                    owner=request.user,
                    files=files,
                    automodere=(
                        request.user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID)
                        or request.user.is_root
                    ),
                )
                if self.form.is_valid():
                    return HttpResponse(str(self.form.errors), status=200)
        return HttpResponse(str(self.form.errors), status=500)


class AlbumView(CanViewMixin, DetailView, FormMixin):
    model = Album
    form_class = SASForm
    pk_url_kwarg = "album_id"
    template_name = "sas/album.jinja"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.asked_page = int(request.GET.get("page", 1))
        except ValueError as e:
            raise Http404 from e
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if "clipboard" not in request.session.keys():
            request.session["clipboard"] = []
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.file:
            self.object.generate_thumbnail()
        self.form = self.get_form()
        if "clipboard" not in request.session.keys():
            request.session["clipboard"] = []
        if request.user.can_edit(self.object):  # Handle the copy-paste functions
            FileView.handle_clipboard(request, self.object)
        parent = SithFile.objects.filter(id=self.object.id).first()
        files = request.FILES.getlist("images")
        if request.user.is_authenticated and request.user.is_subscribed:
            if self.form.is_valid():
                self.form.process(
                    parent=parent,
                    owner=request.user,
                    files=files,
                    automodere=request.user.is_in_group(
                        pk=settings.SITH_GROUP_SAS_ADMIN_ID
                    ),
                )
                if self.form.is_valid():
                    return super().form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse("sas:album", kwargs={"album_id": self.object.id})

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["form"] = self.form
        kwargs["clipboard"] = SithFile.objects.filter(
            id__in=self.request.session["clipboard"]
        )
        kwargs["children_albums"] = list(
            Album.objects.viewable_by(self.request.user)
            .filter(parent_id=self.object.id)
            .order_by("-date")
        )
        return kwargs


# Admin views


class ModerationView(TemplateView):
    template_name = "sas/moderation.jinja"

    def get(self, request, *args, **kwargs):
        if request.user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            return super().get(request, *args, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        if "album_id" not in request.POST:
            raise Http404
        if request.user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            album = get_object_or_404(Album, pk=request.POST["album_id"])
            if "moderate" in request.POST:
                album.moderator = request.user
                album.is_moderated = True
                album.save()
            elif "delete" in request.POST:
                album.delete()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["albums_to_moderate"] = Album.objects.filter(
            is_moderated=False, is_in_sas=True, is_folder=True
        ).order_by("id")
        pictures = Picture.objects.filter(is_moderated=False).select_related("parent")
        kwargs["pictures"] = pictures
        kwargs["albums"] = [p.parent for p in pictures]
        return kwargs


class PictureEditForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = ["name", "parent"]

    parent = make_ajax_field(Picture, "parent", "files", help_text="")


class AlbumEditForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ["name", "date", "file", "parent", "edit_groups"]

    name = forms.CharField(max_length=Album.NAME_MAX_LENGTH, label=_("file name"))
    date = forms.DateField(label=_("Date"), widget=SelectDate, required=True)
    parent = make_ajax_field(Album, "parent", "files", help_text="")
    edit_groups = make_ajax_field(Album, "edit_groups", "groups", help_text="")
    recursive = forms.BooleanField(label=_("Apply rights recursively"), required=False)


class PictureEditView(CanEditMixin, UpdateView):
    model = Picture
    form_class = PictureEditForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "picture_id"


class AlbumEditView(CanEditMixin, UpdateView):
    model = Album
    form_class = AlbumEditForm
    template_name = "core/edit.jinja"
    pk_url_kwarg = "album_id"

    def form_valid(self, form):
        ret = super().form_valid(form)
        if form.cleaned_data["recursive"]:
            self.object.apply_rights_recursively(only_folders=True)
        return ret
