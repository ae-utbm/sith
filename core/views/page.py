#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import Coalesce

# This file contains all the views that concern the page model
from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from core.auth.mixins import (
    CanEditMixin,
    CanEditPropMixin,
    CanViewMixin,
)
from core.models import LockError, Page, PageRev
from core.views.forms import PageForm, PagePropForm
from core.views.widgets.markdown import MarkdownInput


class CanEditPagePropMixin(CanEditPropMixin):
    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        if self.object.is_club_page:
            raise Http404
        return res


class PageListView(ListView):
    model = Page
    template_name = "core/page_list.jinja"

    def get_queryset(self):
        return (
            Page.objects.viewable_by(self.request.user)
            .annotate(
                display_name=Coalesce(
                    Subquery(
                        PageRev.objects.filter(page=OuterRef("id"))
                        .order_by("-date")
                        .values("title")[:1]
                    ),
                    F("name"),
                )
            )
            .select_related("parent")
        )


class PageView(CanViewMixin, DetailView):
    model = Page
    template_name = "core/page_detail.jinja"

    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        if self.object and self.object.need_club_redirection:
            return redirect("club:club_view", club_id=self.object.club.id)
        return res

    def get_object(self):
        self.page = Page.get_page_by_full_name(self.kwargs["page_name"])
        return self.page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "page" not in context:
            context["new_page"] = self.kwargs["page_name"]
        return context


class PageHistView(CanViewMixin, DetailView):
    model = Page
    template_name = "core/page_hist.jinja"
    slug_field = "_full_name"
    slug_url_kwarg = "page_name"
    _cached_object: Page | None = None

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if page.need_club_redirection:
            return redirect("club:club_hist", club_id=page.club.id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        if not self._cached_object:
            self._cached_object = super().get_object()
        return self._cached_object


class PageRevView(CanViewMixin, DetailView):
    model = Page
    template_name = "core/page_detail.jinja"

    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        self.object = self.get_object()

        if self.object is None:
            return redirect("core:page_create", page_name=self.kwargs["page_name"])

        if self.object.need_club_redirection:
            return redirect(
                "club:club_view_rev", club_id=self.object.club.id, rev_id=kwargs["rev"]
            )
        return res

    def get_object(self, *args, **kwargs):
        self.page = Page.get_page_by_full_name(self.kwargs["page_name"])
        return self.page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.page:
            return context | {"new_page": self.kwargs["page_name"]}
        context["page"] = self.page
        context["rev"] = self.page.revisions.filter(id=self.kwargs["rev"]).first()
        return context


class PageCreateView(PermissionRequiredMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = "core/page_prop.jinja"
    permission_required = "core.add_page"

    def get_initial(self):
        init = super().get_initial()
        if "page" not in self.request.GET:
            return init
        page_name = self.request.GET["page"].rsplit("/", maxsplit=1)
        if len(page_name) == 2:
            parent = Page.get_page_by_full_name(page_name[0])
            if parent is not None:
                init["parent"] = parent.id
        init["name"] = page_name[-1]
        return init

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_page"] = True
        return context

    def form_valid(self, form):
        form.instance.set_lock(self.request.user)
        ret = super().form_valid(form)
        return ret


class PagePropView(CanEditPagePropMixin, UpdateView):
    model = Page
    form_class = PagePropForm
    template_name = "core/page_prop.jinja"
    slug_field = "_full_name"
    slug_url_kwarg = "page_name"

    def get_object(self, queryset=None):
        self.page = super().get_object()
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

    def get_object(self, *args, **kwargs):
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
        context = super().get_context_data(**kwargs)
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
        return super().form_valid(form)


class PageEditView(PageEditViewBase):
    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        if self.object and self.object.page.need_club_redirection:
            return redirect("club:club_edit_page", club_id=self.object.page.club.id)
        return res


class PageDeleteView(CanEditPagePropMixin, DeleteView):
    model = Page
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "page_id"

    def get_success_url(self, **kwargs):
        return reverse_lazy("core:page_list")
