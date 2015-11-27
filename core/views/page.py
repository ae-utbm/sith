# This file contains all the views that concern the page model
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

from core.models import Page, PageRevision
from core.views.forms import PagePropForm
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin

class PageListView(ListView):
    model = Page

    def get_context_data(self, **kwargs):
        context = super(PageListView, self).get_context_data(**kwargs)
        return context

# Define some right management callable for user_passes_test
def user_can_view(as_view):
    def guy(*arg, **kwargs):
        res = self.as_view(*arg, **kwargs)

        user = self.request.user
        obj = self.page
        for g in obj.view_group.all():
            if g in user.groups.all():
                print("Allowed")
                return res
        print("Not allowed")
        return res
    return guy

class PageView(CanViewMixin, DetailView):
    model = Page

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

class PagePropView(CanEditPropMixin, UpdateView):
    model = Page
    form_class = PagePropForm
    template_name_suffix = '_prop'

    def get_object(self):
        page_name = self.kwargs['page_name']
        p = Page.get_page_by_full_name(page_name)
        # Create the page if it does not exists
        if p == None:
            parent_name = '/'.join(page_name.split('/')[:-1])
            name = page_name.split('/')[-1]
            if parent_name == "":
                p = Page(name=name, revision=PageRevision())
            else:
                parent = Page.get_page_by_full_name(parent_name)
                p = Page(name=name, parent=parent, revision=PageRevision())
        self.page = p
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PagePropView, self).get_context_data(**kwargs)
        if "page" in context.keys():
            context['tests'] = "PAGE_FOUND : "+context['page'].revision.title
        else:
            context['tests'] = "PAGE_NOT_FOUND"
            context['new_page'] = self.kwargs['page_name']
        return context

class PageEditView(CanEditMixin, UpdateView):
    model = Page
    fields = ['revision.title', 'revision.content',]
    template_name_suffix = '_edit'

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageEditView, self).get_context_data(**kwargs)
        if "page" in context.keys():
            context['tests'] = "PAGE_FOUND : "+context['page'].revision.title
        else:
            context['tests'] = "PAGE_NOT_FOUND"
            context['new_page'] = self.kwargs['page_name']
        return context

