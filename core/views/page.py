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

# This file contains all the views that concern the page model
from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from core.models import LockError, Page, PageRev
from core.views import CanCreateMixin, CanEditMixin, CanEditPropMixin, CanViewMixin
from core.views.forms import MarkdownInput, PageForm, PagePropForm


class CanEditPagePropMixin(CanEditPropMixin):
    def dispatch(self, request, *args, **kwargs):
        res = super(CanEditPagePropMixin, self).dispatch(request, *args, **kwargs)
        if self.object.is_club_page:
            raise Http404
        return res


class PageListView(CanViewMixin, ListView):
    model = Page
    template_name = "core/page_list.jinja"


class PageView(CanViewMixin, DetailView):
    model = Page
    template_name = "core/page_detail.jinja"

    def dispatch(self, request, *args, **kwargs):
        res = super(PageView, self).dispatch(request, *args, **kwargs)
        if self.object and self.object.need_club_redirection:
            return redirect("club:club_view", club_id=self.object.club.id)
        return res

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs["page_name"])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)
        if "page" not in context.keys():
            context["new_page"] = self.kwargs["page_name"]
        return context


class PageHistView(CanViewMixin, DetailView):
    model = Page
    template_name = "core/page_hist.jinja"

    def dispatch(self, request, *args, **kwargs):
        res = super(PageHistView, self).dispatch(request, *args, **kwargs)
        if self.object.need_club_redirection:
            return redirect("club:club_hist", club_id=self.object.club.id)
        return res

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs["page_name"])
        return self.page


class PageRevView(CanViewMixin, DetailView):
    model = Page
    template_name = "core/page_detail.jinja"

    def dispatch(self, request, *args, **kwargs):
        res = super(PageRevView, self).dispatch(request, *args, **kwargs)
        self.object = self.get_object()

        if self.object is None:
            return redirect("core:page_create", page_name=self.kwargs["page_name"])

        if self.object.need_club_redirection:
            return redirect(
                "club:club_view_rev", club_id=self.object.club.id, rev_id=kwargs["rev"]
            )
        return res

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs["page_name"])
        return self.page

    def get_context_data(self, **kwargs):
        context = super(PageRevView, self).get_context_data(**kwargs)
        if self.page is not None:
            context["page"] = self.page
            try:
                rev = self.page.revisions.get(id=self.kwargs["rev"])
                context["rev"] = rev
            except:
                # By passing, the template will just display the normal page without taking revision into account
                pass
        else:
            context["new_page"] = self.kwargs["page_name"]
        return context


class PageCreateView(CanCreateMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = "core/page_prop.jinja"

    def get_initial(self):
        init = {}
        if "page" in self.request.GET.keys():
            page_name = self.request.GET["page"]
            parent_name = "/".join(page_name.split("/")[:-1])
            parent = Page.get_page_by_full_name(parent_name)
            if parent is not None:
                init["parent"] = parent.id
            init["name"] = page_name.split("/")[-1]
        return init

    def get_context_data(self, **kwargs):
        context = super(PageCreateView, self).get_context_data(**kwargs)
        context["new_page"] = True
        return context

    def form_valid(self, form):
        form.instance.set_lock(self.request.user)
        ret = super(PageCreateView, self).form_valid(form)
        return ret


class PagePropView(CanEditPagePropMixin, UpdateView):
    model = Page
    form_class = PagePropForm
    template_name = "core/page_prop.jinja"
    slug_field = "_full_name"
    slug_url_kwarg = "page_name"

    def get_object(self):
        o = super(PagePropView, self).get_object()
        # Create the page if it does not exists
        # if p == None:
        #    parent_name = '/'.join(page_name.split('/')[:-1])
        #    name = page_name.split('/')[-1]
        #    if parent_name == "":
        #        p = Page(name=name)
        #    else:
        #        parent = Page.get_page_by_full_name(parent_name)
        #        p = Page(name=name, parent=parent)
        self.page = o
        try:
            self.page.set_lock_recursive(self.request.user)
        except LockError as e:
            raise e
        return self.page


class PageEditViewBase(CanEditMixin, UpdateView):
    model = PageRev
    form_class = modelform_factory(
        model=PageRev, fields=["title", "content"], widgets={"content": MarkdownInput}
    )
    template_name = "core/pagerev_edit.jinja"

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs["page_name"])
        return self._get_revision()

    def _get_revision(self):
        if self.page is not None:
            # First edit
            if self.page.revisions.all() is None:
                rev = PageRev(author=self.request.user)
                rev.save()
                self.page.revisions.add(rev)
            try:
                self.page.set_lock(self.request.user)
            except LockError as e:
                raise e
            return self.page.revisions.last()
        return None

    def get_context_data(self, **kwargs):
        context = super(PageEditViewBase, self).get_context_data(**kwargs)
        if self.page is not None:
            context["page"] = self.page
        else:
            context["new_page"] = self.kwargs["page_name"]
        return context

    def form_valid(self, form):
        # TODO : factor that, but first make some tests
        rev = form.instance
        new_rev = PageRev(title=rev.title, content=rev.content)
        new_rev.author = self.request.user
        new_rev.page = self.page
        form.instance = new_rev
        return super(PageEditViewBase, self).form_valid(form)


class PageEditView(PageEditViewBase):
    def dispatch(self, request, *args, **kwargs):
        res = super(PageEditView, self).dispatch(request, *args, **kwargs)
        if self.object and self.object.page.need_club_redirection:
            return redirect("club:club_edit_page", club_id=self.object.page.club.id)
        return res


class PageDeleteView(CanEditPagePropMixin, DeleteView):
    model = Page
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "page_id"

    def get_success_url(self, **kwargs):
        return reverse_lazy("core:page_list")
