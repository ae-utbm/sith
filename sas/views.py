from django.shortcuts import render
# from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin, FormView
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings
from django import forms

from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from core.views.forms import SelectUser, LoginForm, SelectDate, SelectDateTime
from core.views.files import send_file
from core.models import SithFile

from sas.models import Picture, Album

class SASForm(forms.Form):
    album_name = forms.CharField(label=_("Add a new album"), max_length=30, required=False)
    images = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}), label=_("Upload images"),
            required=False)

    def process(self, parent, owner, files):
        try:
            if self.cleaned_data['album_name'] != "":
                album = Album(parent=parent, name=self.cleaned_data['album_name'], owner=owner)
                album.clean()
                album.save()
        except Exception as e:
            self.add_error(None, _("Error creating album %(album)s: %(msg)s") %
                    {'album': self.cleaned_data['album_name'], 'msg': str(e.message)})
        for f in files:
            new_file = Picture(parent=parent, name=f.name, file=f, owner=owner, mime_type=f.content_type, size=f._size)
            try:
                new_file.clean()
                # TODO: generate thumbnail
                new_file.save()
            except Exception as e:
                self.add_error(None, _("Error uploading file %(file_name)s: %(msg)s") % {'file_name': f, 'msg': repr(e)})

class SASMainView(FormView):
    form_class = SASForm
    template_name = "sas/main.jinja"
    # success_url = reverse_lazy('sas:main')

    def post(self, request, *args, **kwargs):
        self.form = self.get_form()
        parent = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        files = request.FILES.getlist('images')
        if request.user.is_authenticated() and request.user.is_in_group('ae-membres') and self.form.is_valid():
            self.form.process(parent=parent, owner=request.user, files=files)
            if self.form.is_valid():
                return super(SASMainView, self).form_valid(self.form)
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

class AlbumView(CanViewMixin, FormMixin, DetailView):
    model = Album
    pk_url_kwarg = "album_id"
    template_name = "sas/album.jinja"

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return super(AlbumView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        files = request.FILES.getlist('images')
        if request.user.is_authenticated() and request.user.is_in_group('ae-member') and self.form.is_valid():
            self.form.process(parent=self.object, owner=request.user, files=files)
            if self.form.is_valid():
                return super(AlbumView, self).form_valid(self.form)
        return self.form_invalid(self.form)


