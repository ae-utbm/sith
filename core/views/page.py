# This file contains all the views that concern the page model
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

from core.models import Page, PageRev, LockError
from core.views.forms import PagePropForm
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin

class PageListView(ListView):
    model = Page
    template_name = 'core/page_list.jinja'

    def get_context_data(self, **kwargs):
        context = super(PageListView, self).get_context_data(**kwargs)
        return context

class PageView(CanViewMixin, DetailView):
    model = Page
    template_name = 'core/page_detail.jinja'

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)
        if "page" not in context.keys():
            context['new_page'] = self.kwargs['page_name']
        if self.request.user.is_owner(self.object):
            context['can_edit_prop'] = True
        if self.request.user.can_edit(self.object):
            context['can_edit'] = True

        return context

class PageHistView(CanViewMixin, DetailView):
    model = Page
    template_name = 'core/page_hist.jinja'

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        return self.page

class PageRevView(CanViewMixin, DetailView):
    model = Page
    template_name = 'core/page_detail.jinja'

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageRevView, self).get_context_data(**kwargs)
        if self.page is not None:
            context['page'] = self.page
            try:
                rev = self.page.revisions.get(id=self.kwargs['rev'])
                context['rev'] = rev
            except:
            # By passing, the template will just display the normal page without taking revision into account
                pass
        else:
            context['new_page'] = self.kwargs['page_name']
        return context

class PagePropView(CanEditPropMixin, UpdateView):
    model = Page
    form_class = PagePropForm
    template_name = 'core/page_prop.jinja'

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
        try:
            self.page.set_lock_recursive(self.request.user)
        except LockError as e:
            raise e
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PagePropView, self).get_context_data(**kwargs)
        if "page" not in context.keys():
            context['new_page'] = self.kwargs['page_name']
        return context

class PageEditView(CanEditMixin, UpdateView):
    model = PageRev
    fields = ['title', 'content',]
    template_name = 'core/pagerev_edit.jinja'

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs['page_name'])
        if self.page is not None:
            # First edit
            if self.page.revisions.all() is None:
                rev = PageRev(author=request.user)
                rev.save()
                self.page.revisions.add(rev)
            try:
                self.page.set_lock(self.request.user)
            except LockError as e:
                raise e
            return self.page.revisions.last()
        return None

    def get_context_data(self, **kwargs):
        context = super(PageEditView, self).get_context_data(**kwargs)
        if self.page is not None:
            context['page'] = self.page
        else:
            context['new_page'] = self.kwargs['page_name']
        return context

    def form_valid(self, form):
        # TODO : factor that, but first make some tests
        rev = form.instance
        new_rev = PageRev(title=rev.title,
                          content=rev.content,
                          )
        new_rev.author = self.request.user
        new_rev.page = self.page
        form.instance = new_rev
        return super(PageEditView, self).form_valid(form)

