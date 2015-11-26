# This file contains all the views that concern the page model
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

from core.models import Page

class PageListView(ListView):
    model = Page

    def get_context_data(self, **kwargs):
        context = super(PageListView, self).get_context_data(**kwargs)
        return context

class PageView(DetailView):
    model = Page

    @method_decorator(permission_required('core.can_view'))
    def dispatch(self, *args, **kwargs):
        return super(PageView, self).dispatch(*args, **kwargs)

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)
        if "page" in context.keys():
            context['tests'] = "PAGE_FOUND : "+context['page'].title
        else:
            context['tests'] = "PAGE_NOT_FOUND"
            context['new_page'] = self.kwargs['page_name']
        return context

class PagePropView(UpdateView):
    model = Page
    fields = ['parent', 'name', 'owner_group', 'edit_group', 'view_group', ]
    template_name_suffix = '_prop'

    def __init__(self, *args, **kwargs):
        super(PagePropView, self).__init__(*args, **kwargs)

    def get_object(self):
        page_name = self.kwargs['page_name']
        p = Page.get_page_by_full_name(page_name)
        # Create the page if it does not exists
        if p == None:
            parent_name = '/'.join(page_name.split('/')[:-1])
            name = page_name.split('/')[-1]
            if parent_name == "":
                p = Page(name=name)
            else:
                parent = Page.get_page_by_full_name(parent_name)
                p = Page(name=name, parent=parent)
        self.page = p
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PagePropView, self).get_context_data(**kwargs)
        if "page" in context.keys():
            context['tests'] = "PAGE_FOUND : "+context['page'].title
        else:
            context['tests'] = "PAGE_NOT_FOUND"
            context['new_page'] = self.kwargs['page_name']
        return context

class PageEditView(UpdateView):
    model = Page
    fields = ['title', 'content',]
    template_name_suffix = '_edit'

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageEditView, self).get_context_data(**kwargs)
        if "page" in context.keys():
            context['tests'] = "PAGE_FOUND : "+context['page'].title
        else:
            context['tests'] = "PAGE_NOT_FOUND"
            context['new_page'] = self.kwargs['page_name']
        return context

