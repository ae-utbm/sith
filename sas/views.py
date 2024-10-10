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
from core.views.files import FileView, send_file
from sas.forms import AlbumEditForm, PictureEditForm, SASForm
from sas.models import Album, Picture


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
