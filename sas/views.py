from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin, FormView
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings
from django.forms.models import modelform_factory
from django import forms
from django.core.exceptions import PermissionDenied

from ajax_select import make_ajax_form, make_ajax_field
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField

from io import BytesIO
from PIL import Image

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from core.views.forms import SelectUser, LoginForm, SelectDate, SelectDateTime
from core.views.files import send_file, FileView
from core.models import SithFile, User, Notification, RealGroup

from sas.models import Picture, Album, PeoplePictureRelation

class SASForm(forms.Form):
    album_name = forms.CharField(label=_("Add a new album"), max_length=30, required=False)
    images = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}), label=_("Upload images"),
            required=False)

    def process(self, parent, owner, files, automodere=False):
        notif = False
        try:
            if self.cleaned_data['album_name'] != "":
                album = Album(parent=parent, name=self.cleaned_data['album_name'], owner=owner, is_moderated=automodere)
                album.clean()
                album.save()
                notif = True
        except Exception as e:
            self.add_error(None, _("Error creating album %(album)s: %(msg)s") %
                    {'album': self.cleaned_data['album_name'], 'msg': repr(e)})
        for f in files:
            new_file = Picture(parent=parent, name=f.name, file=f, owner=owner, mime_type=f.content_type, size=f._size,
                    is_folder=False, is_moderated=automodere)
            try:
                new_file.clean()
                new_file.generate_thumbnails()
                new_file.save()
                notif = True
            except Exception as e:
                self.add_error(None, _("Error uploading file %(file_name)s: %(msg)s") % {'file_name': f, 'msg': repr(e)})
        if notif:
            for u in RealGroup.objects.filter(id=settings.SITH_GROUP_SAS_ADMIN_ID).first().users.all():
                if not u.notifications.filter(type="SAS_MODERATION", viewed=False).exists():
                    Notification(user=u, url=reverse("sas:moderation"), type="SAS_MODERATION").save()

class RelationForm(forms.ModelForm):
    class Meta:
        model = PeoplePictureRelation
        fields = ['picture']
        widgets = {'picture': forms.HiddenInput}
    users = AutoCompleteSelectMultipleField('users', show_help_text=False, help_text="", label=_("Add user"), required=False)

class SASMainView(FormView):
    form_class = SASForm
    template_name = "sas/main.jinja"
    success_url = reverse_lazy('sas:main')

    def post(self, request, *args, **kwargs):
        self.form = self.get_form()
        parent = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        files = request.FILES.getlist('images')
        root = User.objects.filter(username="root").first()
        if request.user.is_authenticated() and request.user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID):
            if self.form.is_valid():
                self.form.process(parent=parent, owner=root, files=files, automodere=True)
                if self.form.is_valid():
                    return super(SASMainView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(SASMainView, self).get_context_data(**kwargs)
        kwargs['root_file'] = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        return kwargs

class PictureView(CanViewMixin, DetailView, FormMixin):
    model = Picture
    form_class = RelationForm
    pk_url_kwarg = "picture_id"
    template_name = "sas/picture.jinja"

    def get_initial(self):
        return {'picture': self.object}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if 'rotate_right' in request.GET.keys():
            self.object.rotate(270)
        if 'rotate_left' in request.GET.keys():
            self.object.rotate(90)
        if 'remove_user' in request.GET.keys():
            try:
                user = User.objects.filter(id=int(request.GET['remove_user'])).first()
                if user.id == request.user.id or request.user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID):
                    r = PeoplePictureRelation.objects.filter(user=user, picture=self.object).delete()
            except: pass
        if 'ask_removal' in request.GET.keys():
            self.object.is_moderated = False
            self.object.asked_for_removal = True
            self.object.save()
            return redirect("sas:album", album_id=self.object.parent.id)
        return super(PictureView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if request.user.is_authenticated() and request.user.is_in_group('ae-membres'):
            if self.form.is_valid():
                for uid in self.form.cleaned_data['users']:
                    u = User.objects.filter(id=uid).first()
                    PeoplePictureRelation(user=u,
                            picture=self.form.cleaned_data['picture']).save()
                    if not u.notifications.filter(type="NEW_PICTURES", viewed=False).exists():
                        Notification(user=u, url=reverse("core:user_pictures", kwargs={'user_id': u.id}), type="NEW_PICTURES").save()
                return super(PictureView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(PictureView, self).get_context_data(**kwargs)
        kwargs['form'] = self.form
        return kwargs

    def get_success_url(self):
        return reverse('sas:picture', kwargs={'picture_id': self.object.id})

def send_pict(request, picture_id):
    return send_file(request, picture_id, Picture)

def send_compressed(request, picture_id):
    return send_file(request, picture_id, Picture, "compressed")

def send_thumb(request, picture_id):
    return send_file(request, picture_id, Picture, "thumbnail")

class AlbumView(CanViewMixin, DetailView, FormMixin):
    model = Album
    form_class = SASForm
    pk_url_kwarg = "album_id"
    template_name = "sas/album.jinja"

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if 'clipboard' not in request.session.keys():
            request.session['clipboard'] = []
        return super(AlbumView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if 'clipboard' not in request.session.keys():
            request.session['clipboard'] = []
        if request.user.can_edit(self.object): # Handle the copy-paste functions
            FileView.handle_clipboard(request, self.object)
        parent = SithFile.objects.filter(id=self.object.id).first()
        files = request.FILES.getlist('images')
        if request.user.is_authenticated() and request.user.is_subscribed():
            if self.form.is_valid():
                self.form.process(parent=parent, owner=request.user, files=files,
                        automodere=request.user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID))
                if self.form.is_valid():
                    return super(AlbumView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse('sas:album', kwargs={'album_id': self.object.id})

    def get_context_data(self, **kwargs):
        kwargs = super(AlbumView, self).get_context_data(**kwargs)
        kwargs['form'] = self.form
        kwargs['clipboard'] = SithFile.objects.filter(id__in=self.request.session['clipboard'])
        return kwargs

# Admin views

class ModerationView(TemplateView):
    template_name = "sas/moderation.jinja"

    def get(self, request, *args, **kwargs):
        if request.user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID):
            for k,v in request.GET.items():
                if k[:2] == "a_":
                    try:
                        pict = Picture.objects.filter(id=int(k[2:])).first()
                        if v == "delete":
                            pict.delete()
                        elif v == "moderate":
                            pict.is_moderated = True
                            pict.asked_for_removal = False
                            pict.save()
                    except: pass
            return super(ModerationView, self).get(request, *args, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ModerationView, self).get_context_data(**kwargs)
        kwargs['pictures'] = Picture.objects.filter(is_moderated=False, is_in_sas=True).order_by('id')
        return kwargs

class PictureEditForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields=['name', 'parent']
    parent = make_ajax_field(Picture, 'parent', 'files', help_text="")

class AlbumEditForm(forms.ModelForm):
    class Meta:
        model = Album
        fields=['name', 'file', 'parent']
    parent = make_ajax_field(Album, 'parent', 'files', help_text="")

class PictureEditView(CanEditMixin, UpdateView):
    model=Picture
    form_class=PictureEditForm
    template_name='core/edit.jinja'
    pk_url_kwarg = "picture_id"

class AlbumEditView(CanEditMixin, UpdateView):
    model=Album
    form_class=AlbumEditForm
    template_name='core/edit.jinja'
    pk_url_kwarg = "album_id"

