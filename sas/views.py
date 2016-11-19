from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin, FormView
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings
from django import forms
from django.core.exceptions import PermissionDenied

from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from core.views.forms import SelectUser, LoginForm, SelectDate, SelectDateTime
from core.views.files import send_file
from core.models import SithFile, User

from sas.models import Picture, Album

class SASForm(forms.Form):
    album_name = forms.CharField(label=_("Add a new album"), max_length=30, required=False)
    images = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}), label=_("Upload images"),
            required=False)

    def process(self, parent, owner, files, automodere=False):
        try:
            if self.cleaned_data['album_name'] != "":
                album = Album(parent=parent, name=self.cleaned_data['album_name'], owner=owner, is_moderated=automodere)
                album.clean()
                album.save()
        except Exception as e:
            self.add_error(None, _("Error creating album %(album)s: %(msg)s") %
                    {'album': self.cleaned_data['album_name'], 'msg': str(e.message)})
        for f in files:
            new_file = Picture(parent=parent, name=f.name, file=f, owner=owner, mime_type=f.content_type, size=f._size,
                    is_folder=False, is_moderated=automodere)
            try:
                new_file.clean()
                # TODO: generate thumbnail
                new_file.save()
            except Exception as e:
                self.add_error(None, _("Error uploading file %(file_name)s: %(msg)s") % {'file_name': f, 'msg': repr(e)})

class SASMainView(FormView):
    form_class = SASForm
    template_name = "sas/main.jinja"
    success_url = reverse_lazy('sas:main')

    def post(self, request, *args, **kwargs):
        self.form = self.get_form()
        parent = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        files = request.FILES.getlist('images')
        root = User.objects.filter(username="root").first()
        if request.user.is_authenticated() and request.user.is_in_group(settings.SITH_SAS_ADMIN_GROUP_ID):
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

class PictureView(DetailView, CanViewMixin):
    model = Picture
    pk_url_kwarg = "picture_id"
    template_name = "sas/picture.jinja"

def send_pict(request, picture_id):
    return send_file(request, picture_id, Picture)

class AlbumView(CanViewMixin, DetailView, FormMixin):
    model = Album
    form_class = SASForm
    pk_url_kwarg = "album_id"
    template_name = "sas/album.jinja"

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return super(AlbumView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        parent = SithFile.objects.filter(id=self.object.id).first()
        files = request.FILES.getlist('images')
        if request.user.is_authenticated() and request.user.is_in_group('ae-membres'):
            if self.form.is_valid():
                self.form.process(parent=parent, owner=request.user, files=files)
                if self.form.is_valid():
                    return super(AlbumView, self).form_valid(self.form)
        else:
            self.form.add_error(None, _("You do not have the permission to do that"))
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse_lazy('sas:album', kwargs={'album_id': self.object.id})

    def get_context_data(self, **kwargs):
        kwargs = super(AlbumView, self).get_context_data(**kwargs)
        kwargs['form'] = self.form
        return kwargs

# Admin views

class ModerationView(TemplateView):
    template_name = "sas/moderation.jinja"

    def get(self, request, *args, **kwargs):
        if request.user.is_in_group(settings.SITH_SAS_ADMIN_GROUP_ID):
            for k,v in request.GET.items():
                if k[:7] == "action_":
                    try:
                        pict = Picture.objects.filter(id=int(k[7:])).first()
                        if v == "delete":
                            pict.delete()
                        elif v == "moderate":
                            pict.is_moderated = True
                            pict.save()
                    except: pass
            return super(ModerationView, self).get(request, *args, **kwargs)
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        kwargs = super(ModerationView, self).get_context_data(**kwargs)
        kwargs['pictures'] = [p for p in Picture.objects.filter(is_moderated=False).order_by('id') if p.is_in_sas]
        return kwargs


