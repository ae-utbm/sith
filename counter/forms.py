from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from club.widgets.ajax_select import AutoCompleteSelectClub
from core.models import User
from core.views.forms import NFCTextInput, SelectDate, SelectDateTime
from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultipleGroup,
    AutoCompleteSelectMultipleUser,
    AutoCompleteSelectUser,
)
from counter.models import (
    BillingInfo,
    Counter,
    Customer,
    Eticket,
    Product,
    Refilling,
    ReturnableProduct,
    StudentCard,
)
from counter.widgets.ajax_select import (
    AutoCompleteSelectMultipleCounter,
    AutoCompleteSelectMultipleProduct,
    AutoCompleteSelectProduct,
)


class BillingInfoForm(forms.ModelForm):
    class Meta:
        model = BillingInfo
        fields = [
            "first_name",
            "last_name",
            "address_1",
            "address_2",
            "zip_code",
            "city",
            "country",
            "phone_number",
        ]
        widgets = {
            "phone_number": RegionalPhoneNumberWidget,
            "country": AutoCompleteSelect,
        }


class StudentCardForm(forms.ModelForm):
    """Form for adding student cards"""

    error_css_class = "error"

    class Meta:
        model = StudentCard
        fields = ["uid"]
        widgets = {"uid": NFCTextInput}

    def clean(self):
        cleaned_data = super().clean()
        uid = cleaned_data.get("uid", None)
        if not uid or not StudentCard.is_valid(uid):
            raise forms.ValidationError(_("This UID is invalid"), code="invalid")
        return cleaned_data


class GetUserForm(forms.Form):
    """The Form class aims at providing a valid user_id field in its cleaned data, in order to pass it to some view,
    reverse function, or any other use.

    The Form implements a nice JS widget allowing the user to type a customer account id, or search the database with
    some nickname, first name, or last name (TODO)
    """

    code = forms.CharField(
        label="Code",
        max_length=StudentCard.UID_SIZE,
        required=False,
        widget=NFCTextInput,
    )
    id = forms.CharField(
        label=_("Select user"),
        help_text=None,
        widget=AutoCompleteSelectUser,
        required=False,
    )

    def as_p(self):
        self.fields["code"].widget.attrs["autofocus"] = True
        return super().as_p()

    def clean(self):
        cleaned_data = super().clean()
        customer = None
        if cleaned_data["code"] != "":
            if len(cleaned_data["code"]) == StudentCard.UID_SIZE:
                card = (
                    StudentCard.objects.filter(uid=cleaned_data["code"])
                    .select_related("customer")
                    .first()
                )
                if card is not None:
                    customer = card.customer
            if customer is None:
                customer = Customer.objects.filter(
                    account_id__iexact=cleaned_data["code"]
                ).first()
        elif cleaned_data["id"]:
            customer = Customer.objects.filter(user=cleaned_data["id"]).first()

        if customer is None or not customer.can_buy:
            raise forms.ValidationError(_("User not found"))
        cleaned_data["user_id"] = customer.user.id
        cleaned_data["user"] = customer.user
        return cleaned_data


class RefillForm(forms.ModelForm):
    allowed_refilling_methods = ["CASH", "CARD"]

    error_css_class = "error"
    required_css_class = "required"
    amount = forms.FloatField(
        min_value=0, widget=forms.NumberInput(attrs={"class": "focus"})
    )

    class Meta:
        model = Refilling
        fields = ["amount", "payment_method", "bank"]
        widgets = {"payment_method": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["payment_method"].choices = (
            method
            for method in self.fields["payment_method"].choices
            if method[0] in self.allowed_refilling_methods
        )
        if self.fields["payment_method"].initial not in self.allowed_refilling_methods:
            self.fields["payment_method"].initial = self.allowed_refilling_methods[0]

        if "CHECK" not in self.allowed_refilling_methods:
            del self.fields["bank"]


class CounterEditForm(forms.ModelForm):
    class Meta:
        model = Counter
        fields = ["sellers", "products"]

        widgets = {
            "sellers": AutoCompleteSelectMultipleUser,
            "products": AutoCompleteSelectMultipleProduct,
        }


class ProductEditForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "product_type",
            "code",
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
        help_texts = {
            "description": _(
                "Describe the product. If it's an event's click, "
                "give some insights about it, like the date (including the year)."
            )
        }
        widgets = {
            "product_type": AutoCompleteSelect,
            "buying_groups": AutoCompleteSelectMultipleGroup,
            "club": AutoCompleteSelectClub,
        }

    counters = forms.ModelMultipleChoiceField(
        help_text=None,
        label=_("Counters"),
        required=False,
        widget=AutoCompleteSelectMultipleCounter,
        queryset=Counter.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["counters"].initial = self.instance.counters.all()

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        if self.fields["counters"].initial:
            # Remove the product from all counter it was added to
            # It will then only be added to selected counters
            for counter in self.fields["counters"].initial:
                counter.products.remove(self.instance)
                counter.save()
        for counter in self.cleaned_data["counters"]:
            counter.products.add(self.instance)
            counter.save()
        return ret


class ReturnableProductForm(forms.ModelForm):
    class Meta:
        model = ReturnableProduct
        fields = ["product", "returned_product", "max_return"]
        widgets = {
            "product": AutoCompleteSelectProduct(),
            "returned_product": AutoCompleteSelectProduct(),
        }

    def save(self, commit: bool = True) -> ReturnableProduct:  # noqa FBT
        instance: ReturnableProduct = super().save(commit=commit)
        if commit:
            # This is expensive, but we don't have a task queue to offload it.
            # Hopefully, creations and updates of returnable products
            # occur very rarely
            instance.update_balances()
        return instance


class CashSummaryFormBase(forms.Form):
    begin_date = forms.DateTimeField(
        label=_("Begin date"), widget=SelectDateTime, required=False
    )
    end_date = forms.DateTimeField(
        label=_("End date"), widget=SelectDateTime, required=False
    )


class EticketForm(forms.ModelForm):
    class Meta:
        model = Eticket
        fields = ["product", "banner", "event_title", "event_date"]
        widgets = {
            "product": AutoCompleteSelectProduct,
            "event_date": SelectDate,
        }


class CloseCustomerAccountForm(forms.Form):
    user = forms.ModelChoiceField(
        label=_("Refound this account"),
        help_text=None,
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )
