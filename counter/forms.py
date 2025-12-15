import json
import math
import uuid
from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.db.models import Exists, OuterRef, Q
from django.forms import BaseModelFormSet
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import ClockedSchedule
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from club.models import Club
from club.widgets.ajax_select import AutoCompleteSelectClub
from core.models import User
from core.views.forms import (
    FutureDateTimeField,
    NFCTextInput,
    SelectDate,
    SelectDateTime,
)
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
    InvoiceCall,
    Product,
    Refilling,
    ReturnableProduct,
    ScheduledProductAction,
    Selling,
    StudentCard,
    get_product_actions,
)
from counter.widgets.ajax_select import (
    AutoCompleteSelectMultipleCounter,
    AutoCompleteSelectMultipleProduct,
    AutoCompleteSelectProduct,
    AutoCompleteSelectUserCounter,
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
        widget=AutoCompleteSelectUserCounter,
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


class ScheduledProductActionForm(forms.ModelForm):
    """Form for automatic product archiving.

    The `save` method will update or create tasks using celery-beat.
    """

    required_css_class = "required"
    prefix = "scheduled"

    class Meta:
        model = ScheduledProductAction
        fields = ["task"]
        widgets = {"task": forms.RadioSelect(choices=get_product_actions)}
        labels = {"task": _("Action")}
        help_texts = {"task": ""}

    trigger_at = FutureDateTimeField(
        label=_("Date and time of action"), widget=SelectDateTime
    )
    counters = forms.ModelMultipleChoiceField(
        label=_("New counters"),
        help_text=_("The selected counters will replace the current ones"),
        required=False,
        widget=AutoCompleteSelectMultipleCounter,
        queryset=Counter.objects.all(),
    )

    def __init__(self, *args, product: Product, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:
            self.fields["trigger_at"].initial = self.instance.clocked.clocked_time
            self.fields["counters"].initial = json.loads(self.instance.kwargs).get(
                "counters"
            )

    def clean(self):
        if not self.changed_data or "trigger_at" in self.errors:
            return super().clean()
        if "trigger_at" in self.changed_data:
            if not self.instance.clocked_id:
                self.instance.clocked = ClockedSchedule(
                    clocked_time=self.cleaned_data["trigger_at"]
                )
            else:
                self.instance.clocked.clocked_time = self.cleaned_data["trigger_at"]
            self.instance.clocked.save()
        task_kwargs = {"product_id": self.product.id}
        if (
            self.cleaned_data["task"] == "counter.tasks.change_counters"
            and "counters" in self.changed_data
        ):
            task_kwargs["counters"] = [c.id for c in self.cleaned_data["counters"]]
        self.instance.product = self.product
        self.instance.kwargs = json.dumps(task_kwargs)
        self.instance.name = (
            f"{self.cleaned_data['task']} - {self.product} - {uuid.uuid4()}"
        )
        return super().clean()


class BaseScheduledProductActionFormSet(BaseModelFormSet):
    def __init__(self, *args, product: Product, **kwargs):
        if product.id:
            queryset = (
                product.scheduled_actions.filter(
                    enabled=True, clocked__clocked_time__gt=now()
                )
                .order_by("clocked__clocked_time")
                .select_related("clocked")
            )
        else:
            queryset = ScheduledProductAction.objects.none()
        form_kwargs = {"product": product}
        super().__init__(*args, queryset=queryset, form_kwargs=form_kwargs, **kwargs)

    def delete_existing(self, obj: ScheduledProductAction, commit: bool = True):  # noqa FBT001
        clocked = obj.clocked
        super().delete_existing(obj, commit=commit)
        if commit:
            clocked.delete()


ScheduledProductActionFormSet = forms.modelformset_factory(
    ScheduledProductAction,
    ScheduledProductActionForm,
    formset=BaseScheduledProductActionFormSet,
    absolute_max=None,
    can_delete=True,
    can_delete_extra=False,
    extra=2,
)


class ProductForm(forms.ModelForm):
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

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        if self.instance.id:
            self.fields["counters"].initial = self.instance.counters.all()
        self.action_formset = ScheduledProductActionFormSet(
            *args, product=self.instance, **kwargs
        )

    def is_valid(self):
        return super().is_valid() and self.action_formset.is_valid()

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        self.instance.counters.set(self.cleaned_data["counters"])
        self.action_formset.save()
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


class BasketProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, required=True)
    id = forms.IntegerField(min_value=0, required=True)

    def __init__(
        self,
        customer: Customer,
        counter: Counter,
        allowed_products: dict[int, Product],
        *args,
        **kwargs,
    ):
        self.customer = customer  # Used by formset
        self.counter = counter  # Used by formset
        self.allowed_products = allowed_products
        super().__init__(*args, **kwargs)

    def clean_id(self):
        data = self.cleaned_data["id"]

        # We store self.product so we can use it later on the formset validation
        # And also in the global clean
        self.product = self.allowed_products.get(data, None)
        if self.product is None:
            raise forms.ValidationError(
                _("The selected product isn't available for this user")
            )

        return data

    def clean(self):
        cleaned_data = super().clean()
        if len(self.errors) > 0:
            return

        # Compute prices
        cleaned_data["bonus_quantity"] = 0
        if self.product.tray:
            cleaned_data["bonus_quantity"] = math.floor(
                cleaned_data["quantity"] / Product.QUANTITY_FOR_TRAY_PRICE
            )
        cleaned_data["total_price"] = self.product.price * (
            cleaned_data["quantity"] - cleaned_data["bonus_quantity"]
        )

        return cleaned_data


class BaseBasketForm(forms.BaseFormSet):
    def clean(self):
        self.forms = [form for form in self.forms if form.cleaned_data != {}]

        if len(self.forms) == 0:
            return

        self._check_forms_have_errors()
        self._check_product_are_unique()
        self._check_recorded_products(self[0].customer)
        self._check_enough_money(self[0].counter, self[0].customer)

    def _check_forms_have_errors(self):
        if any(len(form.errors) > 0 for form in self):
            raise forms.ValidationError(_("Submitted basket is invalid"))

    def _check_product_are_unique(self):
        product_ids = {form.cleaned_data["id"] for form in self.forms}
        if len(product_ids) != len(self.forms):
            raise forms.ValidationError(_("Duplicated product entries."))

    def _check_enough_money(self, counter: Counter, customer: Customer):
        self.total_price = sum([data["total_price"] for data in self.cleaned_data])
        if self.total_price > customer.amount:
            raise forms.ValidationError(_("Not enough money"))

    def _check_recorded_products(self, customer: Customer):
        """Check for, among other things, ecocups and pitchers"""
        items = {
            form.cleaned_data["id"]: form.cleaned_data["quantity"]
            for form in self.forms
        }
        ids = list(items.keys())
        returnables = list(
            ReturnableProduct.objects.filter(
                Q(product_id__in=ids) | Q(returned_product_id__in=ids)
            ).annotate_balance_for(customer)
        )
        limit_reached = []
        for returnable in returnables:
            returnable.balance += items.get(returnable.product_id, 0)
        for returnable in returnables:
            dcons = items.get(returnable.returned_product_id, 0)
            returnable.balance -= dcons
            if dcons and returnable.balance < -returnable.max_return:
                limit_reached.append(returnable.returned_product)
        if limit_reached:
            raise forms.ValidationError(
                _(
                    "This user have reached his recording limit "
                    "for the following products : %s"
                )
                % ", ".join([str(p) for p in limit_reached])
            )


BasketForm = forms.formset_factory(
    BasketProductForm, formset=BaseBasketForm, absolute_max=None, min_num=1
)


class InvoiceCallForm(forms.Form):
    def __init__(self, *args, month: date, **kwargs):
        super().__init__(*args, **kwargs)
        self.month = month
        self.clubs = list(
            Club.objects.filter(
                Exists(
                    Selling.objects.filter(
                        club=OuterRef("pk"),
                        date__gte=month,
                        date__lte=month + relativedelta(months=1),
                    )
                )
            ).annotate(
                validated_invoice=Exists(
                    InvoiceCall.objects.filter(
                        club=OuterRef("pk"), month=month, is_validated=True
                    )
                )
            )
        )
        self.fields = {
            str(club.id): forms.BooleanField(
                required=False, initial=club.validated_invoice
            )
            for club in self.clubs
        }

    def save(self):
        invoice_calls = [
            InvoiceCall(
                month=self.month,
                club_id=club.id,
                is_validated=self.cleaned_data.get(str(club.id), False),
            )
            for club in self.clubs
        ]
        InvoiceCall.objects.bulk_create(
            invoice_calls,
            update_conflicts=True,
            update_fields=["is_validated"],
            unique_fields=["month", "club"],
        )
