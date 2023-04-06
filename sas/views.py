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

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectMultipleField
from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import FormMixin, FormView, UpdateView

from core.models import Notification, SithFile, User
from core.views import CanEditMixin, CanViewMixin
from core.views.files import FileView, MultipleImageField, send_file
from core.views.forms import SelectDate
from sas.models import Album, PeoplePictureRelation, Picture


class SASForm(forms.Form):
    album_name = forms.CharField(
        label=_("Add a new album"), max_length=30, required=False
    )
    images = MultipleImageField(
        label=_("Upload images"),
        required=False,
    )

    def process(self, parent, owner, files, automodere=False):
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
                    return super(SASMainView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(SASMainView, self).get_context_data(**kwargs)
        kwargs["categories"] = Album.objects.filter(
            parent__id=settings.SITH_SAS_ROOT_DIR_ID
        ).order_by("id")
        kwargs["latest"] = Album.objects.filter(is_moderated=True).order_by("-id")[:5]
        return kwargs


class PictureView(CanViewMixin, DetailView, FormMixin):
    model = Picture
    form_class = RelationForm
    pk_url_kwarg = "picture_id"
    template_name = "sas/picture.jinja"

    def get_initial(self):
        return {"picture": self.object}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if "rotate_right" in request.GET.keys():
            self.object.rotate(270)
        if "rotate_left" in request.GET.keys():
            self.object.rotate(90)
        if "remove_user" in request.GET.keys():
            try:
                user = User.objects.filter(id=int(request.GET["remove_user"])).first()
                if user.id == request.user.id or request.user.is_in_group(
                    pk=settings.SITH_GROUP_SAS_ADMIN_ID
                ):
                    PeoplePictureRelation.objects.filter(
                        user=user, picture=self.object
                    ).delete()
            except:
                pass
        if "ask_removal" in request.GET.keys():
            self.object.is_moderated = False
            self.object.asked_for_removal = True
            self.object.save()
            return redirect("sas:album", album_id=self.object.parent.id)
        return super(PictureView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if request.user.is_authenticated and request.user.was_subscribed:
            if self.form.is_valid():
                for uid in self.form.cleaned_data["users"]:
                    u = User.objects.filter(id=uid).first()
                    if not u:  # Don't use a non existing user
                        continue
                    if PeoplePictureRelation.objects.filter(
                        user=u, picture=self.form.cleaned_data["picture"]
                    ).exists():  # Avoid existing relation
                        continue
                    PeoplePictureRelation(
                        user=u, picture=self.form.cleaned_data["picture"]
                    ).save()
                    if not u.notifications.filter(
                        type="NEW_PICTURES", viewed=False
                    ).exists():
                        Notification(
                            user=u,
                            url=reverse("core:user_pictures", kwargs={"user_id": u.id}),
                            type="NEW_PICTURES",
                        ).save()
                return super(PictureView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(PictureView, self).get_context_data(**kwargs)
        kwargs["form"] = self.form
        return kwargs

    def get_success_url(self):
        return reverse("sas:picture", kwargs={"picture_id": self.object.id})


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
                    automodere=request.user.is_in_group(
                        pk=settings.SITH_GROUP_SAS_ADMIN_ID
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
    paginate_by = settings.SITH_SAS_IMAGES_PER_PAGE

    def dispatch(self, request, *args, **kwargs):
        try:
            self.asked_page = int(request.GET.get("page", 1))
        except ValueError:
            raise Http404
        return super(AlbumView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if "clipboard" not in request.session.keys():
            request.session["clipboard"] = []
        return super(AlbumView, self).get(request, *args, **kwargs)

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
                    return super(AlbumView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse("sas:album", kwargs={"album_id": self.object.id})

    def get_context_data(self, **kwargs):
        kwargs = super(AlbumView, self).get_context_data(**kwargs)
        kwargs["paginator"] = Paginator(
            self.object.children_pictures.order_by("id"), self.paginate_by
        )
        try:
            kwargs["pictures"] = kwargs["paginator"].page(self.asked_page)
        except InvalidPage:
            raise Http404
        kwargs["form"] = self.form
        kwargs["clipboard"] = SithFile.objects.filter(
            id__in=self.request.session["clipboard"]
        )
        return kwargs


# Admin views


class ModerationView(TemplateView):
    template_name = "sas/moderation.jinja"

    def get(self, request, *args, **kwargs):
        if request.user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            return super(ModerationView, self).get(request, *args, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        if request.user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            try:
                a = Album.objects.filter(id=request.POST["album_id"]).first()
                if "moderate" in request.POST.keys():
                    a.moderator = request.user
                    a.is_moderated = True
                    a.save()
                elif "delete" in request.POST.keys():
                    a.delete()
            except:
                pass
        return super(ModerationView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ModerationView, self).get_context_data(**kwargs)
        kwargs["albums_to_moderate"] = Album.objects.filter(
            is_moderated=False, is_in_sas=True, is_folder=True
        ).order_by("id")
        kwargs["pictures"] = Picture.objects.filter(
            is_moderated=False, is_in_sas=True, is_folder=False
        )
        kwargs["albums"] = Album.objects.filter(
            id__in=kwargs["pictures"].values("parent").distinct("parent")
        )
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
        ret = super(AlbumEditView, self).form_valid(form)
        if form.cleaned_data["recursive"]:
            self.object.apply_rights_recursively(True)
        return ret
