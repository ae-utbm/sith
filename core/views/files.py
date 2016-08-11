# This file contains all the views that concern the page model
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView, FormMixin, DeleteView
from django.contrib.auth.decorators import login_required, permission_required
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django import forms

import os

from core.models import SithFile
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, can_view, not_found

def send_file(request, file_id):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    f = SithFile.objects.filter(id=file_id).first()
    if f is None or f.is_folder:
        return not_found(request)
    if not can_view(f, request.user):
        raise PermissionDenied
    name = f.file.name
    with open(settings.MEDIA_ROOT + name, 'rb') as filename:
        wrapper = FileWrapper(filename)
        response = HttpResponse(wrapper, content_type=f.mime_type)
        response['Content-Length'] = os.path.getsize(settings.MEDIA_ROOT + name)
        response['Content-Disposition'] = 'inline; filename="%s"' % f.name
        return response

class AddFilesForm(forms.Form):
    folder_name = forms.CharField(label=_("Add a new folder"), max_length=30, required=False)
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), label=_("Files"),
            required=False)

    def process(self, parent, owner, files):
        try:
            if self.cleaned_data['folder_name'] != "":
                folder = SithFile(parent=parent, name=self.cleaned_data['folder_name'], owner=owner)
                folder.clean()
                folder.save()
        except Exception as e:
            self.add_error(None, _("Error creating folder %(folder_name)s: %(msg)s") %
                    {'folder_name': self.cleaned_data['folder_name'], 'msg': str(e.message)})
        for f in files:
            new_file = SithFile(parent=parent, name=f.name, file=f, owner=owner, is_folder=False,
                    mime_type=f.content_type, size=f._size)
            try:
                new_file.clean()
                new_file.save()
                print(f.__dict__)
            except Exception as e:
                self.add_error(None, _("Error uploading file %(file_name)s: %(msg)s") %
                        {'file_name': f, 'msg': str(e.message)})

class FileListView(ListView):
    template_name = 'core/file_list.jinja'
    context_object_name = "file_list"

    def get_queryset(self):
        return SithFile.objects.filter(parent=None)

    def get_context_data(self, **kwargs):
        kwargs = super(FileListView, self).get_context_data(**kwargs)
        kwargs['popup'] = ""
        if self.kwargs['popup']:
            kwargs['popup'] = 'popup'
        return kwargs

class FileEditView(CanEditMixin, UpdateView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = 'core/file_edit.jinja'
    context_object_name = "file"

    def get_form_class(self):
        fields = ['name']
        if self.object.is_file:
            fields = ['file'] + fields
        return modelform_factory(SithFile, fields=fields)

    def get_success_url(self):
        if self.kwargs['popup']:
            return reverse('core:file_detail', kwargs={'file_id': self.object.id, 'popup': "popup"})
        return reverse('core:file_detail', kwargs={'file_id': self.object.id, 'popup': ""})

    def get_context_data(self, **kwargs):
        kwargs = super(FileEditView, self).get_context_data(**kwargs)
        kwargs['popup'] = ""
        if self.kwargs['popup']:
            kwargs['popup'] = 'popup'
        return kwargs

class FileEditPropView(CanEditPropMixin, UpdateView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = 'core/file_edit.jinja'
    context_object_name = "file"
    fields = ['parent', 'owner', 'edit_groups', 'view_groups']

    def get_form(self, form_class=None):
        form = super(FileEditPropView, self).get_form(form_class)
        form.fields['parent'].queryset = SithFile.objects.filter(is_folder=True)
        return form

    def get_success_url(self):
        return reverse('core:file_detail', kwargs={'file_id': self.object.id, 'popup': self.kwargs['popup'] or ""})

    def get_context_data(self, **kwargs):
        kwargs = super(FileEditPropView, self).get_context_data(**kwargs)
        kwargs['popup'] = ""
        if self.kwargs['popup']:
            kwargs['popup'] = 'popup'
        return kwargs

class FileView(CanViewMixin, DetailView, FormMixin):
    """This class handle the upload of new files into a folder"""
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = 'core/file_detail.jinja'
    context_object_name = "file"
    form_class = AddFilesForm

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return super(FileView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        files = request.FILES.getlist('file_field')
        if request.user.is_authenticated() and request.user.can_edit(self.object) and self.form.is_valid():
            self.form.process(parent=self.object, owner=request.user, files=files)
            if self.form.is_valid():
                return super(FileView, self).form_valid(self.form)
        return self.form_invalid(self.form)

    def get_success_url(self):
        return reverse('core:file_detail', kwargs={'file_id': self.object.id, 'popup': self.kwargs['popup'] or ""})

    def get_context_data(self, **kwargs):
        kwargs = super(FileView, self).get_context_data(**kwargs)
        kwargs['popup'] = ""
        kwargs['form'] = self.form
        if self.kwargs['popup']:
            kwargs['popup'] = 'popup'
        return kwargs

class FileDeleteView(CanEditPropMixin, DeleteView):
    model = SithFile
    pk_url_kwarg = "file_id"
    template_name = 'core/file_delete_confirm.jinja'
    context_object_name = "file"

    def get_success_url(self):
        self.object.file.delete() # Doing it here or overloading delete() is the same, so let's do it here
        if self.object.parent is None:
            return reverse('core:file_list', kwargs={'popup': self.kwargs['popup'] or ""})
        return reverse('core:file_detail', kwargs={'file_id': self.object.parent.id, 'popup': self.kwargs['popup'] or ""})

    def get_context_data(self, **kwargs):
        kwargs = super(FileDeleteView, self).get_context_data(**kwargs)
        kwargs['popup'] = ""
        if self.kwargs['popup']:
            kwargs['popup'] = 'popup'
        return kwargs

