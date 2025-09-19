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
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import OuterRef, Subquery
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import SafeString
from django.views.generic import CreateView, DetailView, TemplateView
from django.views.generic.edit import FormView, UpdateView

from core.auth.mixins import CanEditMixin, CanViewMixin
from core.models import SithFile, User
from core.views import UseFragmentsMixin
from core.views.files import FileView, send_file
from core.views.mixins import FragmentMixin, FragmentRenderer
from core.views.user import UserTabsMixin
from sas.forms import (
    AlbumCreateForm,
    AlbumEditForm,
    PictureEditForm,
    PictureModerationRequestForm,
    PictureUploadForm,
)
from sas.models import Album, Picture


class AlbumCreateFragment(FragmentMixin, CreateView):
    model = Album
    form_class = AlbumCreateForm
    template_name = "sas/fragments/album_create_form.jinja"
    reload_on_redirect = True

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"owner": self.request.user}

    def render_fragment(
        self, request, owner: User | None = None, **kwargs
    ) -> SafeString:
        self.object = None
        self.owner = owner or self.request.user
        return super().render_fragment(request, **kwargs)

    def get_success_url(self):
        parent = self.object.parent
        parent.__class__ = Album
        return parent.get_absolute_url()


class SASMainView(UseFragmentsMixin, TemplateView):
    template_name = "sas/main.jinja"

    def get_fragments(self) -> dict[str, FragmentRenderer]:
        if not self.request.user.has_perm("sas.add_album"):
            return {}
        form_init = {"parent": SithFile.objects.get(id=settings.SITH_SAS_ROOT_DIR_ID)}
        return {
            "album_create_fragment": AlbumCreateFragment.as_fragment(initial=form_init)
        }

    def get_fragment_data(self) -> dict[str, dict[str, Any]]:
        if not self.request.user.has_perm("sas.add_album"):
            return {}
        root_user = User.objects.get(pk=settings.SITH_ROOT_USER_ID)
        return {"album_create_fragment": {"owner": root_user}}

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


class AlbumView(CanViewMixin, UseFragmentsMixin, DetailView):
    model = Album
    pk_url_kwarg = "album_id"
    template_name = "sas/album.jinja"

    def get_fragments(self) -> dict[str, FragmentRenderer]:
        return {
            "album_create_fragment": AlbumCreateFragment.as_fragment(
                initial={"parent": self.object}
            )
        }

    def dispatch(self, request, *args, **kwargs):
        try:
            self.asked_page = int(request.GET.get("page", 1))
        except ValueError as e:
            raise Http404 from e
        if "clipboard" not in request.session:
            request.session["clipboard"] = []
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.file:
            self.object.generate_thumbnail()
        if request.user.can_edit(self.object):  # Handle the copy-paste functions
            FileView.handle_clipboard(request, self.object)
        return HttpResponseRedirect(self.request.path)

    def get_fragment_data(self) -> dict[str, dict[str, Any]]:
        return {"album_create_fragment": {"owner": self.request.user}}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if ids := self.request.session.get("clipboard", None):
            kwargs["clipboard"] = SithFile.objects.filter(id__in=ids)
        kwargs["upload_form"] = PictureUploadForm()
        # if True, the albums will be fetched with a request to the API
        # if False, the section won't be displayed at all
        kwargs["show_albums"] = (
            Album.objects.viewable_by(self.request.user)
            .filter(parent_id=self.object.id)
            .exists()
        )
        return kwargs


class UserPicturesView(UserTabsMixin, CanViewMixin, DetailView):
    """Display a user's pictures."""

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "sas/user_pictures.jinja"
    current_tab = "pictures"
    queryset = User.objects.annotate(
        last_photo_date=Subquery(
            Picture.objects.filter(people__user=OuterRef("id"))
            .order_by("-date")
            .values("date")[:1]
        )
    ).all()


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


class PictureAskRemovalView(CanViewMixin, DetailView, FormView):
    """View to allow users to ask pictures to be removed."""

    model = Picture
    template_name = "sas/ask_picture_removal.jinja"
    pk_url_kwarg = "picture_id"
    form_class = PictureModerationRequestForm

    def get_form_kwargs(self) -> dict[str, Any]:
        """Add the user and picture to the form kwargs.

        Those are required to create the PictureModerationRequest,
        and aren't part of the form itself
        (picture is a path parameter, and user is the request user).
        """
        return super().get_form_kwargs() | {
            "user": self.request.user,
            "picture": self.object,
        }

    def get_success_url(self) -> str:
        """Return the URL to the album containing the picture."""
        album = Album.objects.filter(pk=self.object.parent_id).first()
        if not album:
            return reverse("sas:main")
        return album.get_absolute_url()

    def form_valid(self, form: PictureModerationRequestForm) -> HttpResponseRedirect:
        form.save()
        self.object.is_moderated = False
        self.object.asked_for_removal = True
        self.object.save()
        return super().form_valid(form)


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
