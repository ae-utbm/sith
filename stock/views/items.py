from django import forms
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView, UpdateView

from club.models import Club
from stock.forms import (
    METADATA_FORMS,
    ItemLineForm,
    StockActionForm,
    StockItemActionFormSet,
    StockItemStockForm,
)
from stock.heper import can_be_edited_by, can_be_view_by
from stock.models import (
    OperationType,
    Stock,
    StockAction,
    StockItemAction,
    StockItemStock,
)


class ItemListView(UserPassesTestMixin, ListView):
    model = StockItemStock
    template_name = "stock/items_list.jinja"
    context_object_name = "items"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        self.stock = get_object_or_404(Stock, pk=kwargs["stock_id"], club=self.club)
        self.is_editor = can_be_edited_by(self.request.user, self.club)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return can_be_view_by(self.request.user, self.club, self.stock)

    def get_queryset(self):
        return (
            StockItemStock.objects.filter(stock=self.stock)
            .select_related("item")
            .order_by("item__name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) | {
            "club": self.club,
            "stock": self.stock,
            "is_editor": self.is_editor,
        }
        return context


class ItemCreateView(UserPassesTestMixin, SuccessMessageMixin, FormView):
    form_class = ItemLineForm
    template_name = "stock/items_create.jinja"
    success_message = _("Item(s) created.")

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        self.stock = get_object_or_404(Stock, pk=kwargs["stock_id"], club=self.club)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return can_be_edited_by(self.request.user, self.club)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "instance": self.stock,
            "queryset": StockItemStock.objects.none(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "club": self.club,
                "stock": self.stock,
                "formset": context["form"],
            }
        )
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "stock:items_list",
            kwargs={"club_id": self.club.id, "stock_id": self.stock.id},
        )


class ItemUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = StockItemStock
    form_class = StockItemStockForm
    pk_url_kwarg = "item_id"
    template_name = "stock/item_edit.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        self.stock = get_object_or_404(Stock, pk=kwargs["stock_id"], club=self.club)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return can_be_edited_by(self.request.user, self.club)

    def get_queryset(self):
        return StockItemStock.objects.filter(stock=self.stock).select_related("item")

    def get_success_url(self):
        return reverse(
            "stock:items_list",
            kwargs={"club_id": self.club.id, "stock_id": self.stock.id},
        )

    def get_success_message(self, cleaned_data):
        return cleaned_data["name"] + _(" edited.")


def update_quantities(stock_items, item_actions, metadata_entries, operation_type):
    match operation_type:
        case OperationType.TransferFrom | OperationType.Refuel:
            for item_action, metadata_entry in zip(
                item_actions, metadata_entries, strict=True
            ):
                item = stock_items[item_action.item_id]
                item_action.quantity_before = item.quantity
                item_action.quantity_after = (
                    item_action.quantity_before + metadata_entry.added_quantity
                )
                item.quantity = item_action.quantity_after
        case _:
            for item_action in item_actions:
                item = stock_items[item_action.item_id]
                item_action.quantity_before = item.quantity
                item.quantity = item_action.quantity_after


def apply_transfer(stock_items, item_actions, metadata_entries, user, source_stock):
    destinations = {}
    for item_action, metadata_entry in zip(item_actions, metadata_entries, strict=True):
        key = (item_action.item.item_id, metadata_entry.new_stock_id)
        if key not in destinations:
            destinations[key], _created = (
                StockItemStock.objects.select_for_update().get_or_create(
                    item_id=key[0],
                    stock_id=key[1],
                    defaults={"quantity": 0},
                )
            )

    destination_stock_action = StockAction(
        action=OperationType.TransferFrom,
        comment=_("Transferred from stock %s") % source_stock.name,
        user=user,
    )
    destination_item_actions = []

    for item_action, metadata_entry in zip(item_actions, metadata_entries, strict=True):
        source_item = stock_items[item_action.item_id]
        destination = destinations[(source_item.item_id, metadata_entry.new_stock_id)]
        quantity = metadata_entry.remove_quantity
        if source_item.quantity - quantity < 0:
            raise forms.ValidationError(
                _("The new quantity cannot be less than zero for item %s.")
                % source_item.name,
                code="lesser_than_zero",
            )

        item_action.quantity_before = source_item.quantity
        source_item.quantity -= quantity
        item_action.quantity_after = source_item.quantity
        destination_item_actions.append(
            StockItemAction(
                action=destination_stock_action,
                item=destination,
                quantity_before=destination.quantity,
                quantity_after=destination.quantity + quantity,
            )
        )
        destination.quantity += quantity
        metadata_entry.other_item_action = destination_item_actions[-1]

    return (
        destination_stock_action,
        list(destinations.values()),
        destination_item_actions,
    )


class ItemActionCreateView(UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = StockAction
    form_class = StockActionForm
    template_name = "stock/action_form.jinja"
    metadata_required = True
    success_message = _("Action complete")

    def test_func(self):
        return can_be_edited_by(self.request.user, self.club)

    def posted_operation_type(self):
        try:
            return int(self.request.POST.get("action"))
        except TypeError, ValueError:
            return None

    def attach_metadata_forms(self, form, active_operation_type=None):
        form.blocks = []
        for operation_type, metadata_form_class in METADATA_FORMS.items():
            kwargs = {
                "prefix": f"{form.prefix}-{operation_type.name.lower()}",
                "empty_permitted": not self.metadata_required,
            }
            if active_operation_type == operation_type.value:
                kwargs.update(data=self.request.POST, files=self.request.FILES)
            metadata_form = metadata_form_class(**kwargs)
            if operation_type == OperationType.TransferTo:
                metadata_form.fields["new_stock"].queryset = Stock.objects.filter(
                    club=self.club
                ).exclude(pk=self.stock.pk)
            form.blocks.append(
                {
                    "action": operation_type.value,
                    "label": operation_type.label,
                    "form": metadata_form,
                }
            )
        return form

    def build_formset(self, instance=None, *, bound=False, active_operation_type=None):
        kwargs = {"instance": instance, "prefix": "item_action"}
        if bound:
            kwargs.update(data=self.request.POST, files=self.request.FILES)
        formset = StockItemActionFormSet(**kwargs)
        item_queryset = (
            StockItemStock.objects.filter(stock=self.stock)
            .select_related("item")
            .order_by("item__name")
        )
        for item_action_form in (*formset.forms, formset.empty_form):
            item_action_form.fields["item"].queryset = item_queryset
            self.attach_metadata_forms(
                item_action_form, active_operation_type if bound else None
            )
        return formset

    def live_forms(self, formset):
        return [
            f
            for f in formset.forms
            if f not in formset.deleted_forms and f.has_changed()
        ]

    def active_metadata_form(self, item_action_form, operation_type):
        return next(
            (
                block["form"]
                for block in item_action_form.blocks
                if block["action"] == operation_type
            ),
            None,
        )

    def render_form(self, form, formset):
        empty = self.attach_metadata_forms(formset.empty_form)
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset, empty_form=empty)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if "formset" not in ctx:
            ctx["formset"] = self.build_formset()
            ctx["empty_form"] = self.attach_metadata_forms(ctx["formset"].empty_form)
        ctx["stock"] = self.stock
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        operation_type = self.object.action
        formset = self.build_formset(
            self.object,
            bound=True,
            active_operation_type=operation_type,
        )

        ok = formset.is_valid()
        if ok:
            for item_action_form in self.live_forms(formset):
                metadata_form = self.active_metadata_form(
                    item_action_form, operation_type
                )
                if metadata_form is not None:
                    ok = metadata_form.is_valid() and ok

        if ok:
            stock_actions, item_actions, metadata_entries = self.serialize_forms(
                form, formset, operation_type
            )

            with transaction.atomic():
                stock_items = (
                    StockItemStock.objects.select_for_update()
                    .select_related("item")
                    .in_bulk(item_action.item_id for item_action in item_actions)
                )
                for item_action in item_actions:
                    item_action.item = stock_items[item_action.item_id]

                try:
                    if operation_type == OperationType.TransferTo:
                        (
                            destination_stock_action,
                            destination_stock_items,
                            destination_item_actions,
                        ) = apply_transfer(
                            stock_items,
                            item_actions,
                            metadata_entries,
                            user=stock_actions[0].user,
                            source_stock=self.stock,
                        )
                        stock_actions.append(destination_stock_action)
                        item_actions.extend(destination_item_actions)
                        stock_items.update(
                            {item.pk: item for item in destination_stock_items}
                        )
                    else:
                        update_quantities(
                            stock_items, item_actions, metadata_entries, operation_type
                        )
                except forms.ValidationError as error:
                    error.message = error.message + _(
                        " Check if the quantity has not changed."
                    )
                    form.add_error(None, error)
                    transaction.set_rollback(True)
                    return self.render_form(form, formset)

                self.save_all(
                    list(stock_items.values()),
                    stock_actions,
                    item_actions,
                    metadata_entries,
                )
            return HttpResponseRedirect(self.get_success_url())
        return self.render_form(form, formset)

    def form_invalid(self, form):
        formset = self.build_formset(
            form.instance,
            bound=True,
            active_operation_type=self.posted_operation_type(),
        )
        return self.render_form(form, formset)

    def save_all(self, stock_items, stock_actions, item_actions, metadata_entries):
        # MariaDB dosen't populate IDs after bulk_create, But we dont use it
        StockAction.objects.bulk_create(stock_actions, batch_size=1000)
        StockItemAction.objects.bulk_create(item_actions, batch_size=1000)
        if metadata_entries:
            type(metadata_entries[0]).objects.bulk_create(
                metadata_entries, batch_size=1000
            )
        StockItemStock.objects.bulk_update(stock_items, ["quantity"], batch_size=1000)

    def serialize_forms(self, form, formset, operation_type):
        stock_action = form.save(commit=False)
        stock_action.user = self.request.user
        item_action_forms = self.live_forms(formset)
        item_actions = [
            item_action_form.save(commit=False)
            for item_action_form in item_action_forms
        ]
        for _item_action_form, item_action in zip(
            item_action_forms, item_actions, strict=True
        ):
            item_action.action = stock_action

        metadata_entries = []
        for item_action_form, item_action in zip(
            item_action_forms, item_actions, strict=True
        ):
            metadata_form = self.active_metadata_form(item_action_form, operation_type)
            if metadata_form is None or (
                not self.metadata_required and not metadata_form.has_changed()
            ):
                continue
            metadata_entry = metadata_form.save(commit=False)
            metadata_entry.item_action = item_action
            if operation_type == OperationType.TransferTo:
                metadata_entry.old_stock = self.stock
            metadata_entries.append(metadata_entry)
        return [stock_action], item_actions, metadata_entries

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        self.stock = get_object_or_404(Stock, pk=kwargs["stock_id"], club=self.club)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "stock:items_list",
            kwargs={"club_id": self.club.id, "stock_id": self.stock.id},
        )
