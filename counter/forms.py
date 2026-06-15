import json
import math
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import ClassVar

from dateutil.relativedelta import relativedelta
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q
from django.forms import BaseModelFormSet
from django.http import HttpRequest
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import ClockedSchedule
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from club.models import Club
from club.widgets.ajax_select import AutoCompleteSelectClub
from core.models import User, UserQuerySet
from core.views import LoginForm
from core.views.forms import (
    FutureDateTimeField,
    NFCTextInput,
    SelectDate,
    SelectDateTime,
)
from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultiple,
    AutoCompleteSelectMultipleGroup,
    AutoCompleteSelectMultipleUser,
    AutoCompleteSelectUser,
)
from counter.models import (
    BillingInfo,
    Counter,
    CounterSellers,
    Customer,
    Eticket,
    InvoiceCall,
    Permanency,
    Price,
    Product,
    ProductFormula,
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
    """Find a user to show its click page."""

    code = forms.CharField(
        label="Code",
        max_length=StudentCard.UID_SIZE,
        required=False,
        widget=NFCTextInput(attrs={"autofocus": True}),
    )
    id = forms.CharField(
        label=_("Select user"), widget=AutoCompleteSelectUser, required=False
    )

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
        cleaned_data["user_id"] = customer.user_id
        cleaned_data["user"] = customer.user
        return cleaned_data


class CounterLoginForm(LoginForm):
    """LoginForm to log a barman in a counter.

    To be able to log in a counter, a user must :

    - be part of the sellers of the given counter
    - not being already logged in any counter
    """

    def __init__(self, *args, request: HttpRequest, counter: Counter, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = counter
        self.request = request

    def confirm_login_allowed(self, user: User):
        super().confirm_login_allowed(user)
        if not self.counter.sellers.contains(user):
            raise ValidationError(
                message=_("You are not a barman of this counter."), code="not_barman"
            )
        if Permanency.objects.filter(end=None, user=user).exists():
            if user in self.request.barmen:
                message = _("You are already logged in this counter.")
            elif user in self.counter.barmen_list:
                message = _("You are already logged in another counter.")
            else:
                message = _("You are already logged on another device")
            raise ValidationError(message=message, code="already_logged_in")


class RefillForm(forms.ModelForm):
    allowed_refilling_methods = [
        Refilling.PaymentMethod.CASH,
        Refilling.PaymentMethod.CARD,
    ]

    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = Refilling
        fields = ["amount", "payment_method"]
        widgets = {"payment_method": forms.RadioSelect}

    def __init__(
        self, *args, counter: Counter, operator: User, customer: Customer, **kwargs
    ):
        super().__init__(*args, **kwargs)
        max_value = settings.SITH_ACCOUNT_MAX_MONEY - customer.amount
        # server-side max_value validation is done by Refilling.clean
        self.fields["amount"].widget.attrs["max"] = max_value
        self.fields["payment_method"].choices = (
            method
            for method in self.fields["payment_method"].choices
            if method[0] in self.allowed_refilling_methods
        )
        if self.fields["payment_method"].initial not in self.allowed_refilling_methods:
            self.fields["payment_method"].initial = self.allowed_refilling_methods[0]
        self.instance.counter = counter
        self.instance.operator = operator
        self.instance.customer = customer


class CounterEditForm(forms.ModelForm):
    class Meta:
        model = Counter
        fields = ["products"]

    sellers_regular = forms.ModelMultipleChoiceField(
        label=_("Regular barmen"),
        help_text=_(
            "Barmen having regular permanences "
            "or frequently giving a hand throughout the semester."
        ),
        queryset=User.objects.all(),
        widget=AutoCompleteSelectMultipleUser,
        required=False,
    )
    sellers_temporary = forms.ModelMultipleChoiceField(
        label=_("Temporary barmen"),
        help_text=_(
            "Barmen who will be there only for a limited period (e.g. for one evening)"
        ),
        queryset=User.objects.all(),
        widget=AutoCompleteSelectMultipleUser,
        required=False,
    )
    field_order = ["sellers_regular", "sellers_temporary", "products"]

    def __init__(self, *args, user: User, instance: Counter, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        # if the user is an admin, he will have access to all products,
        # else only to active products owned by the counter's club
        # or already on the counter
        if user.has_perm("counter.change_counter"):
            self.fields["products"].widget = AutoCompleteSelectMultipleProduct()
        else:
            # updating the queryset of the field also updates the choices of
            # the widget, so it's important to set the queryset after the widget
            self.fields["products"].widget = AutoCompleteSelectMultiple()
            self.fields["products"].queryset = Product.objects.filter(
                Q(club_id=instance.club_id) | Q(counters=instance), archived=False
            ).distinct()
            self.fields["products"].help_text = _(
                "If you want to add a product that is not owned by "
                "your club to this counter, you should ask an admin."
            )
        self.fields["sellers_regular"].initial = self.instance.sellers.filter(
            countersellers__is_regular=True
        ).all()
        self.fields["sellers_temporary"].initial = self.instance.sellers.filter(
            countersellers__is_regular=False
        ).all()

    def clean(self):
        regular: UserQuerySet = self.cleaned_data["sellers_regular"]
        temporary: UserQuerySet = self.cleaned_data["sellers_temporary"]
        duplicates = list(regular.intersection(temporary))
        if duplicates:
            raise ValidationError(
                _(
                    "A user cannot be a regular and a temporary barman "
                    "at the same time, "
                    "but the following users have been defined as both : %(users)s"
                )
                % {"users": ", ".join([u.get_display_name() for u in duplicates])}
            )
        return self.cleaned_data

    def save_sellers(self):
        sellers = []
        for users, is_regular in (
            (self.cleaned_data["sellers_regular"], True),
            (self.cleaned_data["sellers_temporary"], False),
        ):
            sellers.extend(
                [
                    CounterSellers(counter=self.instance, user=u, is_regular=is_regular)
                    for u in users
                ]
            )
        # start by deleting removed CounterSellers objects
        user_ids = [seller.user.id for seller in sellers]
        CounterSellers.objects.filter(
            ~Q(user_id__in=user_ids), counter=self.instance
        ).delete()

        # then create or update the new barmen
        CounterSellers.objects.bulk_create(
            sellers,
            update_conflicts=True,
            update_fields=["is_regular"],
            unique_fields=["user", "counter"],
        )

    def save(self, commit=True):  # noqa: FBT002
        self.instance = super().save(commit=commit)
        if commit and any(
            key in self.changed_data for key in ("sellers_regular", "sellers_temporary")
        ):
            self.save_sellers()
        return self.instance


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

    def set_product(self, product: Product):
        """Set the product to which this form's instance is linked.

        When this form is linked to a ProductForm in the case of a product's creation,
        the product doesn't exist yet, so saving this form as is will result
        in having `{"product_id": null}` in the action kwargs.
        For the creation to be useful, it may be needed to inject the newly created
        product into this form, before saving the latter.
        """
        self.product = product
        kwargs = json.loads(self.instance.kwargs) | {"product_id": self.product.id}
        self.instance.kwargs = json.dumps(kwargs)


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
    extra=0,
)


ProductPriceFormSet = forms.inlineformset_factory(
    parent_model=Product,
    model=Price,
    fields=["amount", "label", "groups", "is_always_shown"],
    widgets={
        "groups": AutoCompleteSelectMultipleGroup,
        "is_always_shown": forms.CheckboxInput(attrs={"class": "switch"}),
    },
    absolute_max=None,
    can_delete_extra=False,
    min_num=1,
    extra=0,
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
            "purchase_price",
            "icon",
            "club",
            "limit_age",
            "tray",
            "clic_limit",
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
            "club": AutoCompleteSelectClub,
            "tray": forms.CheckboxInput(attrs={"class": "switch"}),
        }

    counters = forms.ModelMultipleChoiceField(
        label=_("Counters"),
        required=False,
        widget=AutoCompleteSelectMultipleCounter,
        queryset=Counter.objects.all(),
    )

    def __init__(self, *args, prefix: str | None = None, instance=None, **kwargs):
        super().__init__(*args, prefix=prefix, instance=instance, **kwargs)
        self.fields["name"].widget.attrs["autofocus"] = "autofocus"
        if self.instance.id:
            self.fields["counters"].initial = self.instance.counters.all()
            if hasattr(self.instance, "formula"):
                self.formula_init(self.instance.formula)
        self.price_formset = ProductPriceFormSet(
            *args, instance=self.instance, prefix="price", **kwargs
        )
        self.action_formset = ScheduledProductActionFormSet(
            *args, product=self.instance, prefix="action", **kwargs
        )

    def is_valid(self):
        return (
            super().is_valid()
            and self.price_formset.is_valid()
            and self.action_formset.is_valid()
        )

    def save(self, *args, **kwargs) -> Product:
        product = super().save(*args, **kwargs)
        product.counters.set(self.cleaned_data["counters"])
        # if it's a creation, the product given in the formset
        # wasn't a persisted instance.
        # So if we tried to persist the related objects in the current state,
        # they would be linked to no product, thus be completely useless
        # To make it work, we have to replace
        # the initial product with a persisted one
        for form in self.action_formset:
            form.set_product(product)
        self.action_formset.save()
        self.price_formset.save()
        return product


class ProductFormulaForm(forms.ModelForm):
    class Meta:
        model = ProductFormula
        fields = ["products", "result"]
        widgets = {
            "products": AutoCompleteSelectMultipleProduct,
            "result": AutoCompleteSelectProduct,
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["result"] in cleaned_data["products"]:
            self.add_error(
                None,
                _(
                    "The same product cannot be at the same time "
                    "the result and a part of the formula."
                ),
            )
        return cleaned_data


class ReturnableProductForm(forms.ModelForm):
    class Meta:
        model = ReturnableProduct
        fields = ["product", "returned_product", "max_return"]
        widgets = {
            "product": AutoCompleteSelectProduct,
            "returned_product": AutoCompleteSelectProduct,
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
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )


class BasketItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, required=True)
    price_id = forms.IntegerField(min_value=0, required=True)

    def __init__(self, allowed_prices: dict[int, Price], *args, **kwargs):
        self.allowed_prices = allowed_prices
        super().__init__(*args, **kwargs)

    def clean_price_id(self):
        data = self.cleaned_data["price_id"]

        # We store self.price so we can use it later on the formset validation
        # And also in the global clean
        self.price = self.allowed_prices.get(data, None)
        if self.price is None:
            raise forms.ValidationError(
                _("The selected product isn't available for this user")
            )
        return data

    def clean(self):
        cleaned_data = super().clean()
        if len(self.errors) > 0:
            return cleaned_data

        # Compute prices
        cleaned_data["bonus_quantity"] = 0
        if self.price.product.tray:
            cleaned_data["bonus_quantity"] = math.floor(
                cleaned_data["quantity"] / Product.QUANTITY_FOR_TRAY_PRICE
            )
        cleaned_data["total_price"] = self.price.amount * (
            cleaned_data["quantity"] - cleaned_data["bonus_quantity"]
        )

        return cleaned_data


class BaseBasketForm(forms.BaseFormSet):
    # Minimum amount of money there must be on the account after the transaction
    # If None, the min balance check is skipped
    min_result_balance: ClassVar[int | None] = 0

    def __init__(self, *args, customer: Customer, counter: Counter, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = customer
        self.counter = counter

    def clean(self):
        self.forms = [form for form in self.forms if form.cleaned_data != {}]

        if len(self.forms) == 0:
            return

        self._check_forms_have_errors()
        self._check_product_are_unique()
        self._check_recorded_products()
        self._check_account_balance()

    def _check_forms_have_errors(self):
        if any(len(form.errors) > 0 for form in self):
            raise forms.ValidationError(_("Submitted basket is invalid"))

    def _check_product_are_unique(self):
        price_ids = {form.cleaned_data["price_id"] for form in self.forms}
        if len(price_ids) != len(self.forms):
            raise forms.ValidationError(_("Duplicated product entries."))

    @cached_property
    def total_price(self):
        refill = settings.SITH_COUNTER_PRODUCTTYPE_REFILLING
        total_other = sum(
            form.cleaned_data["total_price"]
            for form in self.forms
            if form.price.product.product_type_id != refill
        )
        total_refill = sum(
            form.cleaned_data["total_price"]
            for form in self.forms
            if form.price.product.product_type_id == refill
        )
        return total_other - total_refill

    def _check_account_balance(self):
        result_balance = self.customer.amount - self.total_price
        if (
            self.min_result_balance is not None
            and self.min_result_balance > result_balance
        ):
            raise forms.ValidationError(_("Not enough money"))
        if result_balance > settings.SITH_ACCOUNT_MAX_MONEY:
            raise ValidationError(
                _("There cannot be more than %(money)d€ on an AE account")
                % {"money": settings.SITH_ACCOUNT_MAX_MONEY}
            )

    def _check_recorded_products(self):
        """Check for, among other things, ecocups and pitchers"""
        items = defaultdict(int)
        for form in self.forms:
            items[form.price.product_id] += form.cleaned_data["quantity"]
        ids = list(items.keys())
        returnables = list(
            ReturnableProduct.objects.filter(
                Q(product_id__in=ids) | Q(returned_product_id__in=ids)
            ).annotate_balance_for(self.customer)
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
    BasketItemForm, formset=BaseBasketForm, absolute_max=None, min_num=1
)


class InvoiceCallForm(forms.Form):
    def __init__(self, *args, month: date, **kwargs):
        super().__init__(*args, **kwargs)
        self.month = month
        month_start = datetime(month.year, month.month, month.day, tzinfo=timezone.utc)
        self.clubs = list(
            Club.objects.filter(
                Exists(
                    Selling.objects.filter(
                        club=OuterRef("pk"),
                        date__gte=month_start,
                        date__lte=month_start + relativedelta(months=1),
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
