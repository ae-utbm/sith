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
import itertools
from datetime import timedelta
from operator import itemgetter

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from core.utils import get_semester_code, get_start_of_semester
from core.views import CanEditMixin, CanViewMixin
from counter.forms import CounterEditForm, ProductEditForm
from counter.models import Counter, Product, ProductType, Refilling, Selling
from counter.utils import is_logged_in_counter
from counter.views.mixins import CounterAdminMixin, CounterAdminTabsMixin


class CounterListView(CounterAdminTabsMixin, CanViewMixin, ListView):
    """A list view for the admins."""

    model = Counter
    template_name = "counter/counter_list.jinja"
    current_tab = "counters"


class CounterEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """Edit a counter's main informations (for the counter's manager)."""

    model = Counter
    form_class = CounterEditForm
    pk_url_kwarg = "counter_id"
    template_name = "core/edit.jinja"
    current_tab = "counters"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        self.edit_club.append(obj.club)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("counter:admin", kwargs={"counter_id": self.object.id})


class CounterEditPropView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """Edit a counter's main informations (for the counter's admin)."""

    model = Counter
    form_class = modelform_factory(Counter, fields=["name", "club", "type"])
    pk_url_kwarg = "counter_id"
    template_name = "core/edit.jinja"
    current_tab = "counters"


class CounterCreateView(CounterAdminTabsMixin, CounterAdminMixin, CreateView):
    """Create a counter (for the admins)."""

    model = Counter
    form_class = modelform_factory(
        Counter,
        fields=["name", "club", "type", "products"],
        widgets={"products": CheckboxSelectMultiple},
    )
    template_name = "core/create.jinja"
    current_tab = "counters"


class CounterDeleteView(CounterAdminTabsMixin, CounterAdminMixin, DeleteView):
    """Delete a counter (for the admins)."""

    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("counter:admin_list")
    current_tab = "counters"


# Product management


class ProductTypeListView(CounterAdminTabsMixin, CounterAdminMixin, ListView):
    """A list view for the admins."""

    model = ProductType
    template_name = "counter/producttype_list.jinja"
    current_tab = "product_types"


class ProductTypeCreateView(CounterAdminTabsMixin, CounterAdminMixin, CreateView):
    """A create view for the admins."""

    model = ProductType
    fields = ["name", "description", "comment", "icon", "priority"]
    template_name = "core/create.jinja"
    current_tab = "products"


class ProductTypeEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """An edit view for the admins."""

    model = ProductType
    template_name = "core/edit.jinja"
    fields = ["name", "description", "comment", "icon", "priority"]
    pk_url_kwarg = "type_id"
    current_tab = "products"


class ProductListView(CounterAdminTabsMixin, CounterAdminMixin, ListView):
    model = Product
    queryset = Product.objects.values("id", "name", "code", "product_type__name")
    template_name = "counter/product_list.jinja"
    ordering = [
        F("product_type__priority").desc(nulls_last=True),
        "product_type",
        "name",
    ]

    def get_context_data(self, **kwargs):
        res = super().get_context_data(**kwargs)
        res["object_list"] = itertools.groupby(
            res["object_list"], key=itemgetter("product_type__name")
        )
        return res


class ArchivedProductListView(ProductListView):
    """A list view for the admins."""

    current_tab = "archive"

    def get_queryset(self):
        return super().get_queryset().filter(archived=True)


class ActiveProductListView(ProductListView):
    """A list view for the admins."""

    current_tab = "products"

    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class ProductCreateView(CounterAdminTabsMixin, CounterAdminMixin, CreateView):
    """A create view for the admins."""

    model = Product
    form_class = ProductEditForm
    template_name = "core/create.jinja"
    current_tab = "products"


class ProductEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """An edit view for the admins."""

    model = Product
    form_class = ProductEditForm
    pk_url_kwarg = "product_id"
    template_name = "core/edit.jinja"
    current_tab = "products"


class RefillingDeleteView(DeleteView):
    """Delete a refilling (for the admins)."""

    model = Refilling
    pk_url_kwarg = "refilling_id"
    template_name = "core/delete_confirm.jinja"

    def dispatch(self, request, *args, **kwargs):
        """We have here a very particular right handling, we can't inherit from CanEditPropMixin."""
        self.object = self.get_object()
        if timezone.now() - self.object.date <= timedelta(
            minutes=settings.SITH_LAST_OPERATIONS_LIMIT
        ) and is_logged_in_counter(request):
            self.success_url = reverse(
                "counter:details", kwargs={"counter_id": self.object.counter.id}
            )
            return super().dispatch(request, *args, **kwargs)
        elif self.object.is_owned_by(request.user):
            self.success_url = reverse(
                "core:user_account", kwargs={"user_id": self.object.customer.user.id}
            )
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class SellingDeleteView(DeleteView):
    """Delete a selling (for the admins)."""

    model = Selling
    pk_url_kwarg = "selling_id"
    template_name = "core/delete_confirm.jinja"

    def dispatch(self, request, *args, **kwargs):
        """We have here a very particular right handling, we can't inherit from CanEditPropMixin."""
        self.object = self.get_object()
        if timezone.now() - self.object.date <= timedelta(
            minutes=settings.SITH_LAST_OPERATIONS_LIMIT
        ) and is_logged_in_counter(request):
            self.success_url = reverse(
                "counter:details", kwargs={"counter_id": self.object.counter.id}
            )
            return super().dispatch(request, *args, **kwargs)
        elif self.object.is_owned_by(request.user):
            self.success_url = reverse(
                "core:user_account", kwargs={"user_id": self.object.customer.user.id}
            )
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class CounterStatView(DetailView, CounterAdminMixin):
    """Show the bar stats."""

    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = "counter/stats.jinja"

    def get_context_data(self, **kwargs):
        """Add stats to the context."""
        counter: Counter = self.object
        semester_start = get_start_of_semester()
        office_hours = counter.get_top_barmen()
        kwargs = super().get_context_data(**kwargs)
        kwargs.update(
            {
                "counter": counter,
                "current_semester": get_semester_code(),
                "total_sellings": counter.get_total_sales(since=semester_start),
                "top_customers": counter.get_top_customers(since=semester_start)[:100],
                "top_barman": office_hours[:100],
                "top_barman_semester": (
                    office_hours.filter(start__gt=semester_start)[:100]
                ),
            }
        )
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            if (
                request.user.is_root
                or request.user.is_board_member
                or self.get_object().is_owned_by(request.user)
            ):
                return super(CanEditMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied


class CounterRefillingListView(CounterAdminTabsMixin, CounterAdminMixin, ListView):
    """List of refillings on a counter."""

    model = Refilling
    template_name = "counter/refilling_list.jinja"
    current_tab = "counters"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.counter = get_object_or_404(Counter, pk=kwargs["counter_id"])
        self.queryset = Refilling.objects.filter(counter__id=self.counter.id)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["counter"] = self.counter
        return kwargs
