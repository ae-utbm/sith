from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
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

class SASMainView(TemplateView):
    template_name = "sas/main.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(SASMainView, self).get_context_data(**kwargs)
        kwargs['root_file'] = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        return kwargs

class AlbumView(DetailView, CanViewMixin):
    model = Album
    pk_url_kwarg = "album_id"
    template_name = "sas/album.jinja"

class PictureView(DetailView, CanViewMixin):
    model = Picture
    pk_url_kwarg = "picture_id"
    template_name = "sas/picture.jinja"

def send_pict(request, picture_id):
    return send_file(request, picture_id, Picture)

