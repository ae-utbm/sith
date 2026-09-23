from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
)
from stock import models
from stock.widgets.ajax_select import StockItemSelect

if TYPE_CHECKING:
    from club.models import Club


class StockForm(forms.ModelForm):
    class Meta:
        model = models.Stock
        fields = ["name", "club"]
        widgets = {"club": forms.HiddenInput}

    def __init__(self, *args, club: Club, **kwargs):
        instance = kwargs.get("instance")
        if instance is not None:
            instance.club = club
        super().__init__(*args, **kwargs)
        self.initial["club"] = club.pk

    def clean(self):
        self.instance.clean()
        return super().clean()


class StockItemStockForm(forms.ModelForm):
    name = forms.CharField(max_length=64, label=_("name"))
    description = forms.CharField(
        required=False, label=_("description"), widget=forms.Textarea
    )
    is_hidden = forms.BooleanField(
        required=False,
        label=_("is hidden"),
        widget=forms.CheckboxInput(attrs={"class": "switch"}),
    )
    is_allow_negative = forms.BooleanField(
        required=False,
        label=_("can be negative"),
        widget=forms.CheckboxInput(attrs={"class": "switch"}),
    )

    class Meta:
        model = models.StockItemStock
        fields = ["name", "description", "is_hidden", "is_allow_negative"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            for name in self.fields:
                self.initial[name] = getattr(self.instance.item, name)

    def save(self, commit=True):  # noqa: FBT002
        if self.instance.pk:
            stock_item = self.instance.item
            for name in ("name", "description", "is_hidden", "is_allow_negative"):
                setattr(stock_item, name, self.cleaned_data[name])
            if commit:
                stock_item.save()
        else:
            stock_item, _ = models.StockItem.objects.get_or_create(
                name=self.cleaned_data["name"],
                defaults={
                    name: self.cleaned_data[name]
                    for name in ("description", "is_hidden", "is_allow_negative")
                },
            )
        self.instance.item = stock_item
        return super().save(commit=commit)


ItemLineForm = forms.inlineformset_factory(
    models.Stock,
    models.StockItemStock,
    form=StockItemStockForm,
    fields=["name", "description", "is_hidden", "is_allow_negative"],
    widgets={
        "is_hidden": forms.CheckboxInput(attrs={"class": "switch"}),
        "is_allow_negative": forms.CheckboxInput(attrs={"class": "switch"}),
    },
    can_delete_extra=False,
    can_delete=False,
    min_num=1,
    validate_min=True,
    extra=0,
)

AUTHORIZED_OPERATION_TYPES = [
    models.OperationType.Refuel,
    models.OperationType.TransferTo,
    models.OperationType.Overwrite,
]

HIDDEN_QUANTITY_ACTIONS = (
    models.OperationType.Refuel,
    models.OperationType.TransferTo,
)


class StockActionForm(forms.ModelForm):
    class Meta:
        model = models.StockAction
        fields = ["comment", "action"]
        widgets = {
            "action": forms.Select,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Alpine
        self.fields["action"].choices = [
            (operation_type.value, operation_type.label)
            for operation_type in AUTHORIZED_OPERATION_TYPES
        ]
        self.fields["action"].widget.attrs["x-model"] = "action"


StockItemActionFormSet = forms.inlineformset_factory(
    models.StockAction,
    models.StockItemAction,
    fields=["quantity_after", "item"],
    can_delete_extra=False,
    can_delete=False,
    min_num=1,
    validate_min=True,
    extra=0,
    widgets={
        "quantity_after": forms.NumberInput(
            attrs={
                "x-show": "!"
                + str([str(action.value) for action in HIDDEN_QUANTITY_ACTIONS])
                + ".includes(action)"
            }
        ),
        "item": StockItemSelect,
    },
)


class RefuelMetadataForm(forms.ModelForm):
    added_quantity = forms.DecimalField(
        required=True,
        min_value=0,
        label=_("Quantity added"),
        widget=forms.NumberInput(),
    )

    def get_initial_for_field(self, field, field_name):
        if field_name == "added_quantity" and self.instance.pk:
            return self.instance.added_quantity
        return super().get_initial_for_field(field, field_name)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("added_quantity") is not None:
            self.instance.added_quantity = cleaned["added_quantity"]
        return cleaned

    class Meta:
        model = models.StockRefuelMetadata
        fields = ["unit_price"]


class TransferMetadataForm(forms.ModelForm):
    transfer_quantity = forms.DecimalField(
        required=True,
        min_value=0,
        label=_("Quantity transferred"),
        widget=forms.NumberInput(),
    )

    def get_initial_for_field(self, field, field_name):
        if field_name == "transfer_quantity" and self.instance.pk:
            return self.instance.remove_quantity
        return super().get_initial_for_field(field, field_name)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("transfer_quantity") is not None:
            self.instance.added_quantity = cleaned["transfer_quantity"]
        return cleaned

    class Meta:
        model = models.StockTransferMetadata
        fields = ["new_stock"]
        widgets = {
            "new_stock": AutoCompleteSelect,
        }


METADATA_FORMS = {
    models.OperationType.Refuel: RefuelMetadataForm,
    models.OperationType.TransferTo: TransferMetadataForm,
}
