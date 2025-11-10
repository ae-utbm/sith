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
from core.models import Page, PageRev
from core.views.forms import PageForm, PagePropForm
from core.views.widgets.markdown import MarkdownInput


class PageNotFound(Http404):
    """Http404 Exception, but specifically for when the not found object is a Page."""

    def __init__(self, page_name: str):
        self.page_name = page_name


def get_page_or_404(full_name: str) -> Page:
    """Like Django's get_object_or_404, but for Page, and with a custom 404 exception."""
    page = Page.objects.filter(_full_name=full_name).first()
    if not page:
        raise PageNotFound(full_name)
    return page


class PageListView(ListView):
    model = Page
    template_name = "core/page/list.jinja"

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


class BasePageDetailView(CanViewMixin, DetailView):
    model = Page
    slug_url_kwarg = "page_name"
    _cached_object: Page | None = None

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if page.need_club_redirection:
            return redirect("club:club_view", club_id=page.club.id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        if not self._cached_object:
            full_name = self.kwargs.get(self.slug_url_kwarg)
            self._cached_object = get_page_or_404(full_name)
        return self._cached_object

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "last_revision": self.object.revisions.last()
        }


class PageView(BasePageDetailView):
    template_name = "core/page/detail.jinja"


class PageHistView(BasePageDetailView):
    template_name = "core/page/history.jinja"


class PageRevView(BasePageDetailView):
    template_name = "core/page/detail.jinja"

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if page.need_club_redirection:
            return redirect(
                "club:club_view_rev", club_id=page.club.id, rev_id=kwargs["rev"]
            )
        self.revision = get_object_or_404(page.revisions, id=self.kwargs["rev"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"revision": self.revision}


class PageCreateView(PermissionRequiredMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = "core/create.jinja"
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

    def form_valid(self, form):
        form.instance.set_lock(self.request.user)
        ret = super().form_valid(form)
        return ret


class CanEditPagePropMixin(CanEditPropMixin):
    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        if self.object.is_club_page:
            raise Http404
        return res


class PagePropView(CanEditPagePropMixin, UpdateView):
    model = Page
    form_class = PagePropForm
    template_name = "core/page/prop.jinja"

    def get_object(self, queryset=None):
        self.page = get_page_or_404(full_name=self.kwargs["page_name"])
        self.page.set_lock_recursive(self.request.user)
        return self.page


class PageEditViewBase(CanEditMixin, UpdateView):
    model = PageRev
    form_class = modelform_factory(
        model=PageRev, fields=["title", "content"], widgets={"content": MarkdownInput}
    )
    template_name = "core/page/edit.jinja"

    def get_object(self, *args, **kwargs):
        self.page = get_page_or_404(full_name=self.kwargs["page_name"])
        self.page.set_lock(self.request.user)
        return self.page.revisions.last()

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"page": self.page}

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
        self.object = self.get_object()
        if self.object and self.object.page.need_club_redirection:
            return redirect("club:club_edit_page", club_id=self.object.page.club.id)
        return super().dispatch(request, *args, **kwargs)


class PageDeleteView(CanEditPagePropMixin, DeleteView):
    model = Page
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "page_id"
    success_url = reverse_lazy("core:page_list")
