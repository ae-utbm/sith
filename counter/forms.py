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

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField
from django import forms
from django.utils.translation import gettext_lazy as _

from core.views.forms import SelectDate, TzAwareDateTimeField
from counter.models import (
    BillingInfo,
    Counter,
    Customer,
    Eticket,
    Product,
    Refilling,
    StudentCard,
)


class BillingInfoForm(forms.ModelForm):
    class Meta:
        model = BillingInfo
        exclude = ["customer"]


class StudentCardForm(forms.ModelForm):
    """
    Form for adding student cards
    Only used for user profile since CounterClick is to complicated
    """

    class Meta:
        model = StudentCard
        fields = ["uid"]

    def clean(self):
        cleaned_data = super(StudentCardForm, self).clean()
        uid = cleaned_data.get("uid", None)
        if not uid or not StudentCard.is_valid(uid):
            raise forms.ValidationError(_("This UID is invalid"), code="invalid")
        return cleaned_data


class GetUserForm(forms.Form):
    """
    The Form class aims at providing a valid user_id field in its cleaned data, in order to pass it to some view,
    reverse function, or any other use.

    The Form implements a nice JS widget allowing the user to type a customer account id, or search the database with
    some nickname, first name, or last name (TODO)
    """

    code = forms.CharField(
        label="Code", max_length=StudentCard.UID_SIZE, required=False
    )
    id = AutoCompleteSelectField(
        "users", required=False, label=_("Select user"), help_text=None
    )

    def as_p(self):
        self.fields["code"].widget.attrs["autofocus"] = True
        return super(GetUserForm, self).as_p()

    def clean(self):
        cleaned_data = super(GetUserForm, self).clean()
        cus = None
        if cleaned_data["code"] != "":
            if len(cleaned_data["code"]) == StudentCard.UID_SIZE:
                card = StudentCard.objects.filter(uid=cleaned_data["code"])
                if card.exists():
                    cus = card.first().customer
            if cus is None:
                cus = Customer.objects.filter(
                    account_id__iexact=cleaned_data["code"]
                ).first()
        elif cleaned_data["id"] is not None:
            cus = Customer.objects.filter(user=cleaned_data["id"]).first()
        if cus is None or not cus.can_buy:
            raise forms.ValidationError(_("User not found"))
        cleaned_data["user_id"] = cus.user.id
        cleaned_data["user"] = cus.user
        return cleaned_data


class RefillForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"
    amount = forms.FloatField(
        min_value=0, widget=forms.NumberInput(attrs={"class": "focus"})
    )

    class Meta:
        model = Refilling
        fields = ["amount", "payment_method", "bank"]


class CounterEditForm(forms.ModelForm):
    class Meta:
        model = Counter
        fields = ["sellers", "products"]

    sellers = make_ajax_field(Counter, "sellers", "users", help_text="")
    products = make_ajax_field(Counter, "products", "products", help_text="")


class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "product_type",
            "code",
            "parent_product",
            "buying_groups",
            "purchase_price",
            "selling_price",
            "special_selling_price",
            "icon",
            "club",
            "limit_age",
            "tray",
            "archived",
        ]

    parent_product = AutoCompleteSelectField(
        "products", show_help_text=False, label=_("Parent product"), required=False
    )
    buying_groups = AutoCompleteSelectMultipleField(
        "groups",
        show_help_text=False,
        help_text="",
        label=_("Buying groups"),
        required=True,
    )
    club = AutoCompleteSelectField("clubs", show_help_text=False)
    counters = AutoCompleteSelectMultipleField(
        "counters",
        show_help_text=False,
        help_text="",
        label=_("Counters"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ProductEditForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["counters"].initial = [
                str(c.id) for c in self.instance.counters.all()
            ]

    def save(self, *args, **kwargs):
        ret = super(ProductEditForm, self).save(*args, **kwargs)
        if self.fields["counters"].initial:
            for cid in self.fields["counters"].initial:
                c = Counter.objects.filter(id=int(cid)).first()
                c.products.remove(self.instance)
                c.save()
        for cid in self.cleaned_data["counters"]:
            c = Counter.objects.filter(id=int(cid)).first()
            c.products.add(self.instance)
            c.save()
        return ret


class CashSummaryFormBase(forms.Form):
    begin_date = TzAwareDateTimeField(label=_("Begin date"), required=False)
    end_date = TzAwareDateTimeField(label=_("End date"), required=False)


class EticketForm(forms.ModelForm):
    class Meta:
        model = Eticket
        fields = ["product", "banner", "event_title", "event_date"]
        widgets = {"event_date": SelectDate}

    product = AutoCompleteSelectField(
        "products", show_help_text=False, label=_("Product"), required=True
    )
