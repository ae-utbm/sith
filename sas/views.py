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

from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse_lazy, reverse
from core.views.forms import SelectDate
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import UpdateView, FormMixin, FormView
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from django.core.exceptions import PermissionDenied

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectMultipleField

from core.views import CanViewMixin, CanEditMixin
from core.views.files import send_file, FileView
from core.models import SithFile, User, Notification, RealGroup

from sas.models import Picture, Album, PeoplePictureRelation


class SASForm(forms.Form):
    album_name = forms.CharField(
        label=_("Add a new album"), max_length=30, required=False
    )
    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
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
                size=f._size,
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
        if request.user.is_authenticated() and request.user.is_in_group(
            settings.SITH_GROUP_SAS_ADMIN_ID
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
                    settings.SITH_GROUP_SAS_ADMIN_ID
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
        if request.user.is_authenticated() and request.user.was_subscribed:
            if self.form.is_valid():
                for uid in self.form.cleaned_data["users"]:
                    u = User.objects.filter(id=uid).first()
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
        if request.user.is_authenticated() and request.user.is_subscribed:
            if self.form.is_valid():
                self.form.process(
                    parent=parent,
                    owner=request.user,
                    files=files,
                    automodere=request.user.is_in_group(
                        settings.SITH_GROUP_SAS_ADMIN_ID
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
        if request.user.is_authenticated() and request.user.is_subscribed:
            if self.form.is_valid():
                self.form.process(
                    parent=parent,
                    owner=request.user,
                    files=files,
                    automodere=request.user.is_in_group(
                        settings.SITH_GROUP_SAS_ADMIN_ID
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
        kwargs["form"] = self.form
        kwargs["clipboard"] = SithFile.objects.filter(
            id__in=self.request.session["clipboard"]
        )
        return kwargs


# Admin views


class ModerationView(TemplateView):
    template_name = "sas/moderation.jinja"

    def get(self, request, *args, **kwargs):
        if request.user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID):
            return super(ModerationView, self).get(request, *args, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        if request.user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID):
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
