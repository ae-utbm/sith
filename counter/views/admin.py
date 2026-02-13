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
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from core.auth.mixins import CanViewMixin
from core.utils import get_semester_code, get_start_of_semester
from counter.forms import (
    CloseCustomerAccountForm,
    CounterEditForm,
    ProductForm,
    ProductFormulaForm,
    ReturnableProductForm,
)
from counter.models import (
    Counter,
    Product,
    ProductFormula,
    ProductType,
    Refilling,
    ReturnableProduct,
    Selling,
)
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
    template_name = "counter/product_type_list.jinja"
    current_tab = "product_types"
    context_object_name = "product_types"


class ProductTypeCreateView(CounterAdminTabsMixin, CounterAdminMixin, CreateView):
    """A create view for the admins."""

    model = ProductType
    fields = ["name", "description", "comment", "icon"]
    template_name = "core/create.jinja"
    current_tab = "products"


class ProductTypeEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """An edit view for the admins."""

    model = ProductType
    template_name = "core/edit.jinja"
    fields = ["name", "description", "comment", "icon"]
    pk_url_kwarg = "type_id"
    current_tab = "products"


class ProductListView(CounterAdminTabsMixin, CounterAdminMixin, TemplateView):
    current_tab = "products"
    template_name = "counter/product_list.jinja"


class ProductCreateView(CounterAdminTabsMixin, CounterAdminMixin, CreateView):
    """A create view for the admins."""

    model = Product
    form_class = ProductForm
    template_name = "counter/product_form.jinja"
    current_tab = "products"


class ProductEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """An edit view for the admins."""

    model = Product
    form_class = ProductForm
    pk_url_kwarg = "product_id"
    template_name = "counter/product_form.jinja"
    current_tab = "products"


class ProductFormulaListView(CounterAdminTabsMixin, PermissionRequiredMixin, ListView):
    model = ProductFormula
    queryset = ProductFormula.objects.select_related("result").prefetch_related(
        "products"
    )
    template_name = "counter/formula_list.jinja"
    current_tab = "formulas"
    permission_required = "counter.view_productformula"


class ProductFormulaCreateView(
    CounterAdminTabsMixin, PermissionRequiredMixin, CreateView
):
    model = ProductFormula
    form_class = ProductFormulaForm
    pk_url_kwarg = "formula_id"
    template_name = "core/create.jinja"
    current_tab = "formulas"
    success_url = reverse_lazy("counter:product_formula_list")
    permission_required = "counter.add_productformula"


class ProductFormulaEditView(
    CounterAdminTabsMixin, PermissionRequiredMixin, UpdateView
):
    model = ProductFormula
    form_class = ProductFormulaForm
    pk_url_kwarg = "formula_id"
    template_name = "core/edit.jinja"
    current_tab = "formulas"
    success_url = reverse_lazy("counter:product_formula_list")
    permission_required = "counter.change_productformula"


class ProductFormulaDeleteView(
    CounterAdminTabsMixin, PermissionRequiredMixin, DeleteView
):
    model = ProductFormula
    pk_url_kwarg = "formula_id"
    template_name = "core/delete_confirm.jinja"
    current_tab = "formulas"
    success_url = reverse_lazy("counter:product_formula_list")
    permission_required = "counter.delete_productformula"

    def get_context_data(self, **kwargs):
        obj_name = self.object.result.name
        return super().get_context_data(**kwargs) | {
            "object_name": _("%(formula)s (formula)") % {"formula": obj_name},
            "help_text": _(
                "This action will only delete the formula, "
                "but not the %(product)s product itself."
            )
            % {"product": obj_name},
        }


class ReturnableProductListView(
    CounterAdminTabsMixin, PermissionRequiredMixin, ListView
):
    model = ReturnableProduct
    queryset = model.objects.select_related("product", "returned_product")
    template_name = "counter/returnable_list.jinja"
    current_tab = "returnable_products"
    permission_required = "counter.view_returnableproduct"


class ReturnableProductCreateView(
    CounterAdminTabsMixin, PermissionRequiredMixin, CreateView
):
    form_class = ReturnableProductForm
    template_name = "core/create.jinja"
    current_tab = "returnable_products"
    success_url = reverse_lazy("counter:returnable_list")
    permission_required = "counter.add_returnableproduct"


class ReturnableProductUpdateView(
    CounterAdminTabsMixin, PermissionRequiredMixin, UpdateView
):
    model = ReturnableProduct
    pk_url_kwarg = "returnable_id"
    queryset = model.objects.select_related("product", "returned_product")
    form_class = ReturnableProductForm
    template_name = "core/edit.jinja"
    current_tab = "returnable_products"
    success_url = reverse_lazy("counter:returnable_list")
    permission_required = "counter.change_returnableproduct"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "object_name": _("returnable product : %(returnable)s -> %(returned)s")
            % {
                "returnable": self.object.product.name,
                "returned": self.object.returned_product.name,
            }
        }


class ReturnableProductDeleteView(
    CounterAdminTabsMixin, PermissionRequiredMixin, DeleteView
):
    model = ReturnableProduct
    pk_url_kwarg = "returnable_id"
    queryset = model.objects.select_related("product", "returned_product")
    template_name = "core/delete_confirm.jinja"
    current_tab = "returnable_products"
    success_url = reverse_lazy("counter:returnable_list")
    permission_required = "counter.delete_returnableproduct"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "object_name": _("returnable product : %(returnable)s -> %(returned)s")
            % {
                "returnable": self.object.product.name,
                "returned": self.object.returned_product.name,
            }
        }


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


class CounterStatView(PermissionRequiredMixin, DetailView):
    """Show the bar stats."""

    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = "counter/stats.jinja"
    permission_required = "counter.view_counter_stats"

    def get_context_data(self, **kwargs):
        """Add stats to the context."""
        counter: Counter = self.object
        start_date = get_start_of_semester()
        semester_start = datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            tzinfo=get_current_timezone(),
        )
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


class RefoundAccountView(UserPassesTestMixin, FormView):
    """Create a selling with the same amount as the current user money."""

    template_name = "counter/refound_account.jinja"
    form_class = CloseCustomerAccountForm

    def test_func(self):
        return self.request.user.is_root or self.request.user.is_in_group(
            pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID
        )

    def form_valid(self, form):
        self.customer = form.cleaned_data["user"]
        self.create_selling()
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path

    def create_selling(self):
        with transaction.atomic():
            uprice = self.customer.customer.amount
            refound_club_counter = Counter.objects.get(
                id=settings.SITH_COUNTER_REFOUND_ID
            )
            refound_club = refound_club_counter.club
            s = Selling(
                label=_("Refound account"),
                unit_price=uprice,
                quantity=1,
                seller=self.request.user,
                customer=self.customer.customer,
                club=refound_club,
                counter=refound_club_counter,
                product=Product.objects.get(id=settings.SITH_PRODUCT_REFOUND_ID),
            )
            s.save()
