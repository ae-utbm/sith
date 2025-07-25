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
from __future__ import annotations

import base64
import os
import random
import string
from datetime import date, datetime, timedelta
from datetime import timezone as tz
from decimal import Decimal
from typing import Literal, Self

from dict2xml import dict2xml
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Exists, F, OuterRef, Q, QuerySet, Subquery, Sum, Value
from django.db.models.functions import Coalesce, Concat, Length
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from ordered_model.models import OrderedModel
from phonenumber_field.modelfields import PhoneNumberField

from club.models import Club
from core.fields import ResizedImageField
from core.models import Group, Notification, User
from core.utils import get_start_of_semester
from counter.apps import PAYMENT_METHOD
from counter.fields import CurrencyField
from subscription.models import Subscription


def get_eboutic() -> Counter:
    return Counter.objects.filter(type="EBOUTIC").order_by("id").first()


class CustomerQuerySet(models.QuerySet):
    def update_amount(self) -> int:
        """Update the amount of all customers selected by this queryset.

        The result is given as the sum of all refills
        minus the sum of all purchases paid with the AE account.

        Returns:
            The number of updated rows.

        Warning:
            The execution time of this query grows really quickly.
            When updating 500 customers, it may take around a second.
            If you try to update all customers at once, the execution time
            goes up to tens of seconds.
            Use this either on a small subset of the `Customer` table,
            or execute it inside an independent task
            (like a Celery task or a management command).
        """
        money_in = Subquery(
            Refilling.objects.filter(customer=OuterRef("pk"))
            .values("customer_id")  # group by customer
            .annotate(res=Sum(F("amount"), default=0))
            .values("res")
        )
        money_out = Subquery(
            Selling.objects.filter(
                customer=OuterRef("pk"), payment_method="SITH_ACCOUNT"
            )
            .values("customer_id")
            .annotate(res=Sum(F("unit_price") * F("quantity"), default=0))
            .values("res")
        )
        return self.update(amount=Coalesce(money_in - money_out, Decimal("0")))


class Customer(models.Model):
    """Customer data of a User.

    It adds some basic customers' information, such as the account ID, and
    is used by other accounting classes as reference to the customer, rather than using User.
    """

    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    account_id = models.CharField(_("account id"), max_length=10, unique=True)
    amount = CurrencyField(_("amount"), default=0)

    objects = CustomerQuerySet.as_manager()

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customers")
        ordering = ["account_id"]

    def __str__(self):
        return "%s - %s" % (self.user.username, self.account_id)

    def save(self, *args, allow_negative=False, **kwargs):
        """is_selling : tell if the current action is a selling
        allow_negative : ignored if not a selling. Allow a selling to put the account in negative
        Those two parameters avoid blocking the save method of a customer if his account is negative.
        """
        if self.amount < 0 and not allow_negative:
            raise ValidationError(_("Not enough money"))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:user_account", kwargs={"user_id": self.user.pk})

    def update_returnable_balance(self):
        """Update all returnable balances of this user to their real amount."""

        def purchases_qs(outer_ref: Literal["product_id", "returned_product_id"]):
            return (
                Selling.objects.filter(customer=self, product=OuterRef(outer_ref))
                .values("product")
                .annotate(quantity=Sum("quantity", default=0))
                .values("quantity")
            )

        balances = (
            ReturnableProduct.objects.annotate_balance_for(self)
            .annotate(
                nb_cons=Coalesce(Subquery(purchases_qs("product_id")), 0),
                nb_dcons=Coalesce(Subquery(purchases_qs("returned_product_id")), 0),
            )
            .annotate(new_balance=F("nb_cons") - F("nb_dcons"))
            .values("id", "new_balance")
        )
        updated_balances = [
            ReturnableProductBalance(
                customer=self, returnable_id=b["id"], balance=b["new_balance"]
            )
            for b in balances
        ]
        ReturnableProductBalance.objects.bulk_create(
            updated_balances,
            update_conflicts=True,
            update_fields=["balance"],
            unique_fields=["customer", "returnable"],
        )

    @property
    def can_buy(self) -> bool:
        """Check if whether this customer has the right to purchase any item.

        This must be not confused with the Product.can_be_sold_to(user)
        method as the present method returns an information
        about a customer whereas the other tells something
        about the relation between a User (not a Customer,
        don't mix them) and a Product.
        """
        subscription = self.user.subscriptions.order_by("subscription_end").last()
        if subscription is None:
            return False
        return (date.today() - subscription.subscription_end) < timedelta(days=90)

    @classmethod
    def get_or_create(cls, user: User) -> tuple[Customer, bool]:
        """Work in pretty much the same way as the usual get_or_create method,
        but with the default field replaced by some under the hood.

        If the user has an account, return it as is.
        Else create a new account with no money on it and a new unique account id

        Example : ::

            user = User.objects.get(pk=1)
            account, created = Customer.get_or_create(user)
            if created:
                print(f"created a new account with id {account.id}")
            else:
                print(f"user has already an account, with {account.id} € on it"
        """
        if hasattr(user, "customer"):
            return user.customer, False

        # account_id are always a number with a letter appended
        account_id = (
            Customer.objects.order_by(Length("account_id"), "account_id")
            .values("account_id")
            .last()
        )
        if account_id is None:
            # legacy from the old site
            account = cls.objects.create(user=user, account_id="1504a")
            return account, True

        account_id = account_id["account_id"]
        account_num = int(account_id[:-1])
        while Customer.objects.filter(account_id=account_id).exists():
            # when entering the first iteration, we are using an already existing account id
            # so the loop should always execute at least one time
            account_num += 1
            account_id = f"{account_num}{random.choice(string.ascii_lowercase)}"

        account = cls.objects.create(user=user, account_id=account_id)
        return account, True

    def get_full_url(self):
        return f"https://{settings.SITH_URL}{self.get_absolute_url()}"


class BillingInfo(models.Model):
    """Represent the billing information of a user, which are required
    by the 3D-Secure v2 system used by the etransaction module.
    """

    customer = models.OneToOneField(
        Customer, related_name="billing_infos", on_delete=models.CASCADE
    )

    # declaring surname and name even though they are already defined
    # in User add some redundancy, but ensures that the billing infos
    # shall stay correct, whatever shenanigans the user commits on its profile
    first_name = models.CharField(_("First name"), max_length=22)
    last_name = models.CharField(_("Last name"), max_length=22)
    address_1 = models.CharField(_("Address 1"), max_length=50)
    address_2 = models.CharField(_("Address 2"), max_length=50, blank=True, null=True)
    zip_code = models.CharField(_("Zip code"), max_length=16)  # code postal
    city = models.CharField(_("City"), max_length=50)
    country = CountryField(blank_label=_("Country"))

    # This table was created during the A22 semester.
    # However, later on, CA asked for the phone number to be added to the billing info.
    # As the table was already created, this new field had to be nullable,
    # even tough it is required by the bank and shouldn't be null.
    # If one day there is no null phone number remaining,
    # please make the field non-nullable.
    phone_number = PhoneNumberField(_("Phone number"), null=True, blank=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def to_3dsv2_xml(self) -> str:
        """Convert the data from this model into a xml usable
        by the online paying service of the Crédit Agricole bank.
        see : `https://www.ca-moncommerce.com/espace-client-mon-commerce/up2pay-e-transactions/ma-documentation/manuel-dintegration-focus-3ds-v2/principes-generaux/#integration-3dsv2-developpeur-webmaster`.
        """
        data = {
            "Address": {
                "FirstName": self.first_name,
                "LastName": self.last_name,
                "Address1": self.address_1,
                "ZipCode": self.zip_code,
                "City": self.city,
                "CountryCode": self.country.numeric,  # ISO-3166-1 numeric code
                "MobilePhone": self.phone_number.as_national.replace(" ", ""),
                "CountryCodeMobilePhone": f"+{self.phone_number.country_code}",
            }
        }
        if self.address_2:
            data["Address"]["Address2"] = self.address_2
        xml = dict2xml(data, wrap="Billing", newlines=False)
        return '<?xml version="1.0" encoding="UTF-8" ?>' + xml


class AccountDumpQuerySet(models.QuerySet):
    def ongoing(self) -> Self:
        """Filter dump operations that are not completed yet."""
        return self.filter(dump_operation=None)


class AccountDump(models.Model):
    """The process of dumping an account."""

    customer = models.ForeignKey(
        Customer, related_name="dumps", on_delete=models.CASCADE
    )
    warning_mail_sent_at = models.DateTimeField(
        help_text=_(
            "When the mail warning that the account was about to be dumped was sent."
        )
    )
    warning_mail_error = models.BooleanField(
        default=False,
        help_text=_("Set this to True if the warning mail received an error"),
    )
    dump_operation = models.OneToOneField(
        "Selling",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=_("The operation that emptied the account."),
    )

    objects = AccountDumpQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=Q(dump_operation=None),
                name="unique_ongoing_dump",
            ),
        ]

    def __str__(self):
        status = "ongoing" if self.dump_operation is None else "finished"
        return f"{self.customer} - {status}"

    @cached_property
    def amount(self):
        return (
            self.dump_operation.unit_price
            if self.dump_operation
            else self.customer.amount
        )


class ProductType(OrderedModel):
    """A product type.

    Useful only for categorizing.
    """

    name = models.CharField(_("name"), max_length=30)
    description = models.TextField(_("description"), default="")
    comment = models.TextField(
        _("comment"),
        default="",
        help_text=_("A text that will be shown on the eboutic."),
    )
    icon = ResizedImageField(
        height=70, force_format="WEBP", upload_to="products", null=True, blank=True
    )

    class Meta:
        verbose_name = _("product type")
        ordering = ["order"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("counter:product_type_list")

    def is_owned_by(self, user):
        """Method to see if that object can be edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_in_group(pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)


class Product(models.Model):
    """A product, with all its related information."""

    QUANTITY_FOR_TRAY_PRICE = 6

    name = models.CharField(_("name"), max_length=64)
    description = models.TextField(_("description"), default="")
    product_type = models.ForeignKey(
        ProductType,
        related_name="products",
        verbose_name=_("product type"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    code = models.CharField(_("code"), max_length=16, blank=True)
    purchase_price = CurrencyField(
        _("purchase price"),
        help_text=_("Initial cost of purchasing the product"),
    )
    selling_price = CurrencyField(_("selling price"))
    special_selling_price = CurrencyField(
        _("special selling price"),
        help_text=_("Price for barmen during their permanence"),
    )
    icon = ResizedImageField(
        height=70,
        force_format="WEBP",
        upload_to="products",
        null=True,
        blank=True,
        verbose_name=_("icon"),
    )
    club = models.ForeignKey(
        Club, related_name="products", verbose_name=_("club"), on_delete=models.CASCADE
    )
    limit_age = models.IntegerField(_("limit age"), default=0)
    tray = models.BooleanField(_("tray price"), default=False)
    buying_groups = models.ManyToManyField(
        Group, related_name="products", verbose_name=_("buying groups"), blank=True
    )
    archived = models.BooleanField(_("archived"), default=False)

    class Meta:
        verbose_name = _("product")

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse("counter:product_list")

    def is_owned_by(self, user):
        """Method to see if that object can be edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_in_group(
            pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID
        ) or user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)

    def can_be_sold_to(self, user: User) -> bool:
        """Check if whether the user given in parameter has the right to buy
        this product or not.

        This must be not confused with the Customer.can_buy()
        method as the present method returns an information
        about the relation between a User and a Product,
        whereas the other tells something about a Customer
        (and not a user, they are not the same model).

        Returns:
            True if the user can buy this product else False

        Warning:
            This performs a db query, thus you can quickly have
            a N+1 queries problem if you call it in a loop.
            Hopefully, you can avoid that if you prefetch the buying_groups :

            ```python
            user = User.objects.get(username="foobar")
            products = [
                p
                for p in Product.objects.prefetch_related("buying_groups")
                if p.can_be_sold_to(user)
            ]
            ```
        """
        buying_groups = list(self.buying_groups.all())
        if not buying_groups:
            return True
        return any(user.is_in_group(pk=group.id) for group in buying_groups)

    @property
    def profit(self):
        return self.selling_price - self.purchase_price


class CounterQuerySet(models.QuerySet):
    def annotate_has_barman(self, user: User) -> Self:
        """Annotate the queryset with the `user_is_barman` field.

        For each counter, this field has value True if the user
        is a barman of this counter, else False.

        Args:
            user: the user we want to check if he is a barman

        Examples:
            ```python
            sli = User.objects.get(username="sli")
            counters = (
                Counter.objects
                .annotate_has_barman(sli)  # add the user_has_barman boolean field
                .filter(has_annotated_barman=True)  # keep only counters where this user is barman
            )
            print("Sli est barman dans les comptoirs suivants :")
            for counter in counters:
                print(f"- {counter.name}")
            ```
        """
        subquery = user.counters.filter(pk=OuterRef("pk"))
        return self.annotate(has_annotated_barman=Exists(subquery))

    def annotate_is_open(self) -> Self:
        """Annotate tue queryset with the `is_open` field.

        For each counter, if `is_open=True`, then the counter is currently opened.
        Else the counter is closed.
        """
        return self.annotate(
            is_open=Exists(
                Permanency.objects.filter(counter_id=OuterRef("pk"), end=None)
            )
        )

    def handle_timeout(self) -> int:
        """Disconnect the barmen who are inactive in the given counters.

        Returns:
            The number of affected rows (ie, the number of timeouted permanences)
        """
        timeout = timezone.now() - timedelta(minutes=settings.SITH_BARMAN_TIMEOUT)
        return Permanency.objects.filter(
            counter__in=self, end=None, activity__lt=timeout
        ).update(end=F("activity"))


class Counter(models.Model):
    name = models.CharField(_("name"), max_length=30)
    club = models.ForeignKey(
        Club, related_name="counters", verbose_name=_("club"), on_delete=models.CASCADE
    )
    products = models.ManyToManyField(
        Product, related_name="counters", verbose_name=_("products"), blank=True
    )
    type = models.CharField(
        _("counter type"),
        max_length=255,
        choices=[("BAR", _("Bar")), ("OFFICE", _("Office")), ("EBOUTIC", _("Eboutic"))],
    )
    sellers = models.ManyToManyField(
        User, verbose_name=_("sellers"), related_name="counters", blank=True
    )
    edit_groups = models.ManyToManyField(
        Group, related_name="editable_counters", blank=True
    )
    view_groups = models.ManyToManyField(
        Group, related_name="viewable_counters", blank=True
    )
    token = models.CharField(_("token"), max_length=30, null=True, blank=True)

    objects = CounterQuerySet.as_manager()

    class Meta:
        verbose_name = _("counter")
        permissions = [("view_counter_stats", "Can view counter stats")]

    def __str__(self):
        return self.name

    def __getattribute__(self, name: str):
        if name == "edit_groups":
            return Group.objects.filter(
                name=self.club.unix_name + settings.SITH_BOARD_SUFFIX
            ).all()
        return object.__getattribute__(self, name)

    def get_absolute_url(self) -> str:
        if self.type == "EBOUTIC":
            return reverse("eboutic:main")
        return reverse("counter:details", kwargs={"counter_id": self.id})

    def is_owned_by(self, user: User) -> bool:
        if user.is_anonymous:
            return False
        mem = self.club.get_membership_for(user)
        if mem and mem.role >= settings.SITH_CLUB_ROLES_ID["Treasurer"]:
            return True
        return user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)

    def can_be_viewed_by(self, user: User) -> bool:
        return (
            self.type == "BAR"
            or user.is_root
            or user.is_in_group(pk=self.club.board_group_id)
            or user in self.sellers.all()
        )

    def gen_token(self) -> None:
        """Generate a new token for this counter."""
        self.token = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(30)
        )
        self.save()

    @cached_property
    def barmen_list(self) -> list[User]:
        """Returns the barman list as list of User."""
        return [
            p.user for p in self.permanencies.filter(end=None).select_related("user")
        ]

    def get_random_barman(self) -> User:
        """Return a random user being currently a barman."""
        return random.choice(self.barmen_list)

    def update_activity(self) -> None:
        """Update the barman activity to prevent timeout."""
        self.permanencies.filter(end=None).update(activity=timezone.now())

    def can_refill(self) -> bool:
        """Show if the counter authorize the refilling with physic money."""
        if self.type != "BAR":
            return False
        # at least one of the barmen is in the AE board
        ae = Club.objects.get(id=settings.SITH_MAIN_CLUB_ID)
        return any(ae.get_membership_for(barman) for barman in self.barmen_list)

    def get_top_barmen(self) -> QuerySet:
        """Return a QuerySet querying the office hours stats of all the barmen of all time
        of this counter, ordered by descending number of hours.

        Each element of the QuerySet corresponds to a barman and has the following data :
            - the full name (first name + last name) of the barman
            - the nickname of the barman
            - the promo of the barman
            - the total number of office hours the barman did attend
        """
        name_expr = Concat(F("user__first_name"), Value(" "), F("user__last_name"))
        return (
            self.permanencies.exclude(end=None)
            .annotate(
                name=name_expr, nickname=F("user__nick_name"), promo=F("user__promo")
            )
            .values("user", "name", "nickname", "promo")
            .annotate(perm_sum=Sum(F("end") - F("start")))
            .exclude(perm_sum=None)
            .order_by("-perm_sum")
        )

    def get_top_customers(self, since: datetime | date | None = None) -> QuerySet:
        """Return a QuerySet querying the money spent by customers of this counter
        since the specified date, ordered by descending amount of money spent.

        Each element of the QuerySet corresponds to a customer and has the following data :

        - the full name (first name + last name) of the customer
        - the nickname of the customer
        - the amount of money spent by the customer

        Args:
            since: timestamp from which to perform the calculation
        """
        if since is None:
            since = get_start_of_semester()
        if isinstance(since, date):
            since = datetime(since.year, since.month, since.day, tzinfo=tz.utc)
        name_expr = Concat(
            F("customer__user__first_name"), Value(" "), F("customer__user__last_name")
        )
        return (
            self.sellings.filter(date__gte=since)
            .annotate(
                name=name_expr,
                nickname=F("customer__user__nick_name"),
                promo=F("customer__user__promo"),
                user=F("customer__user"),
            )
            .values("user", "promo", "name", "nickname")
            .annotate(
                selling_sum=Sum(
                    F("unit_price") * F("quantity"), output_field=CurrencyField()
                )
            )
            .filter(selling_sum__gt=0)
            .order_by("-selling_sum")
        )

    def get_total_sales(self, since: datetime | date | None = None) -> CurrencyField:
        """Compute and return the total turnover of this counter since the given date.

        By default, the date is the start of the current semester.

        Args:
            since: timestamp from which to perform the calculation

        Returns:
            Total revenue earned at this counter.
        """
        if since is None:
            since = get_start_of_semester()
        if isinstance(since, date):
            since = datetime(since.year, since.month, since.day, tzinfo=tz.utc)
        return self.sellings.filter(date__gte=since).aggregate(
            total=Sum(
                F("quantity") * F("unit_price"),
                default=0,
                output_field=CurrencyField(),
            )
        )["total"]

    def customer_is_barman(self, customer: Customer | User) -> bool:
        """Check if this counter is a `bar` and if the customer is currently logged in.
        This is useful to compute special prices."""

        # Customer and User are two different tables,
        # but they share the same primary key
        return self.type == "BAR" and any(b.pk == customer.pk for b in self.barmen_list)

    def get_products_for(self, customer: Customer) -> list[Product]:
        """
        Get all allowed products for the provided customer on this counter
        Prices will be annotated
        """

        products = self.products.select_related("product_type").prefetch_related(
            "buying_groups"
        )

        # Only include age appropriate products
        age = customer.user.age
        if customer.user.is_banned_alcohol:
            age = min(age, 17)
        products = products.filter(limit_age__lte=age)

        # Compute special price for customer if he is a barmen on that bar
        if self.customer_is_barman(customer):
            products = products.annotate(price=F("special_selling_price"))
        else:
            products = products.annotate(price=F("selling_price"))

        return [
            product
            for product in products.all()
            if product.can_be_sold_to(customer.user)
        ]


class RefillingQuerySet(models.QuerySet):
    def annotate_total(self) -> Self:
        """Annotate the Queryset with the total amount.

        The total is just the sum of the amounts for each row.
        If no grouping is involved (like in most queries),
        this is just the same as doing nothing and fetching the
        `amount` attribute.

        However, it may be useful when there is a `group by` clause
        in the query, or when other models are queried and having
        a common interface is helpful (e.g. `Selling.objects.annotate_total()`
        and `Refilling.objects.annotate_total()` will both have the `total` field).
        """
        return self.annotate(total=Sum("amount"))


class Refilling(models.Model):
    """Handle the refilling."""

    counter = models.ForeignKey(
        Counter, related_name="refillings", blank=False, on_delete=models.CASCADE
    )
    amount = CurrencyField(_("amount"))
    operator = models.ForeignKey(
        User,
        related_name="refillings_as_operator",
        blank=False,
        on_delete=models.CASCADE,
    )
    customer = models.ForeignKey(
        Customer, related_name="refillings", blank=False, on_delete=models.CASCADE
    )
    date = models.DateTimeField(_("date"))
    payment_method = models.CharField(
        _("payment method"),
        max_length=255,
        choices=PAYMENT_METHOD,
        default="CARD",
    )
    bank = models.CharField(
        _("bank"), max_length=255, choices=settings.SITH_COUNTER_BANK, default="OTHER"
    )
    is_validated = models.BooleanField(_("is validated"), default=False)

    objects = RefillingQuerySet.as_manager()

    class Meta:
        verbose_name = _("refilling")

    def __str__(self):
        return "Refilling: %.2f for %s" % (
            self.amount,
            self.customer.user.get_display_name(),
        )

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()
        self.full_clean()
        if not self.is_validated:
            self.customer.amount += self.amount
            self.customer.save()
            self.is_validated = True
        if self.customer.user.preferences.notify_on_refill:
            Notification(
                user=self.customer.user,
                url=reverse(
                    "core:user_account_detail",
                    kwargs={
                        "user_id": self.customer.user.id,
                        "year": self.date.year,
                        "month": self.date.month,
                    },
                ),
                param=str(self.amount),
                type="REFILLING",
            ).save()
        super().save(*args, **kwargs)

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_owner(self.counter) and self.payment_method != "CARD"

    def delete(self, *args, **kwargs):
        self.customer.amount -= self.amount
        self.customer.save()
        super().delete(*args, **kwargs)


class SellingQuerySet(models.QuerySet):
    def annotate_total(self) -> Self:
        """Annotate the Queryset with the total amount of the sales.

        The total is considered as the sum of (unit_price * quantity).
        """
        return self.annotate(total=Sum(F("unit_price") * F("quantity")))


class Selling(models.Model):
    """Handle the sellings."""

    # We make sure that sellings have a way begger label than any product name is allowed to
    label = models.CharField(_("label"), max_length=128)
    product = models.ForeignKey(
        Product,
        related_name="sellings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    counter = models.ForeignKey(
        Counter,
        related_name="sellings",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    club = models.ForeignKey(
        Club, related_name="sellings", null=True, blank=False, on_delete=models.SET_NULL
    )
    unit_price = CurrencyField(_("unit price"))
    quantity = models.IntegerField(_("quantity"))
    seller = models.ForeignKey(
        User,
        related_name="sellings_as_operator",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    customer = models.ForeignKey(
        Customer,
        related_name="buyings",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    date = models.DateTimeField(_("date"))
    payment_method = models.CharField(
        _("payment method"),
        max_length=255,
        choices=[("SITH_ACCOUNT", _("Sith account")), ("CARD", _("Credit card"))],
        default="SITH_ACCOUNT",
    )
    is_validated = models.BooleanField(_("is validated"), default=False)

    objects = SellingQuerySet.as_manager()

    class Meta:
        verbose_name = _("selling")

    def __str__(self):
        return (
            f"Selling: {self.quantity} x {self.label} "
            f"({self.quantity * self.unit_price} €) "
            f"for {self.customer.user.get_display_name()}"
        )

    def save(self, *args, allow_negative=False, **kwargs):
        """allow_negative : Allow this selling to use more money than available for this user."""
        if not self.date:
            self.date = timezone.now()
        self.full_clean()
        if not self.is_validated:
            self.customer.amount -= self.quantity * self.unit_price
            self.customer.save(allow_negative=allow_negative)
            self.is_validated = True
        user = self.customer.user
        if user.was_subscribed:
            if (
                self.product
                and self.product.id == settings.SITH_PRODUCT_SUBSCRIPTION_ONE_SEMESTER
            ):
                sub = Subscription(
                    member=user,
                    subscription_type="un-semestre",
                    payment_method="EBOUTIC",
                    location="EBOUTIC",
                )
                sub.subscription_start = Subscription.compute_start()
                sub.subscription_start = Subscription.compute_start(
                    duration=settings.SITH_SUBSCRIPTIONS[sub.subscription_type][
                        "duration"
                    ]
                )
                sub.subscription_end = Subscription.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[sub.subscription_type][
                        "duration"
                    ],
                    start=sub.subscription_start,
                )
                sub.save()
            elif (
                self.product
                and self.product.id == settings.SITH_PRODUCT_SUBSCRIPTION_TWO_SEMESTERS
            ):
                sub = Subscription(
                    member=user,
                    subscription_type="deux-semestres",
                    payment_method="EBOUTIC",
                    location="EBOUTIC",
                )
                sub.subscription_start = Subscription.compute_start()
                sub.subscription_start = Subscription.compute_start(
                    duration=settings.SITH_SUBSCRIPTIONS[sub.subscription_type][
                        "duration"
                    ]
                )
                sub.subscription_end = Subscription.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[sub.subscription_type][
                        "duration"
                    ],
                    start=sub.subscription_start,
                )
                sub.save()
        if user.preferences.notify_on_click:
            Notification(
                user=user,
                url=reverse(
                    "core:user_account_detail",
                    kwargs={
                        "user_id": user.id,
                        "year": self.date.year,
                        "month": self.date.month,
                    },
                ),
                param="%d x %s" % (self.quantity, self.label),
                type="SELLING",
            ).save()
        super().save(*args, **kwargs)
        if hasattr(self.product, "eticket"):
            self.send_mail_customer()

    def is_owned_by(self, user: User) -> bool:
        if user.is_anonymous:
            return False
        return self.payment_method != "CARD" and user.is_owner(self.counter)

    def can_be_viewed_by(self, user: User) -> bool:
        if (
            not hasattr(self, "customer") or self.customer is None
        ):  # Customer can be set to Null
            return False
        return user == self.customer.user

    def delete(self, *args, **kwargs):
        if self.payment_method == "SITH_ACCOUNT":
            self.customer.amount += self.quantity * self.unit_price
            self.customer.save()
        super().delete(*args, **kwargs)
        self.customer.update_returnable_balance()

    def send_mail_customer(self):
        event = self.product.eticket.event_title or _("Unknown event")
        subject = _("Eticket bought for the event %(event)s") % {"event": event}
        message_html = _(
            "You bought an eticket for the event %(event)s.\nYou can download it directly from this link %(eticket)s.\nYou can also retrieve all your e-tickets on your account page %(url)s."
        ) % {
            "event": event,
            "url": (
                f'<a href="{self.customer.get_full_url()}">'
                f"{self.customer.get_full_url()}</a>"
            ),
            "eticket": (
                f'<a href="{self.get_eticket_full_url()}">'
                f"{self.get_eticket_full_url()}</a>"
            ),
        }
        message_txt = _(
            "You bought an eticket for the event %(event)s.\n"
            "You can download it directly from this link %(eticket)s.\n"
            "You can also retrieve all your e-tickets on your account page %(url)s."
        ) % {
            "event": event,
            "url": self.customer.get_full_url(),
            "eticket": self.get_eticket_full_url(),
        }
        self.customer.user.email_user(
            subject, message_txt, html_message=message_html, fail_silently=True
        )

    def get_eticket_full_url(self):
        eticket_url = reverse("counter:eticket_pdf", kwargs={"selling_id": self.id})
        return f"https://{settings.SITH_URL}{eticket_url}"


class Permanency(models.Model):
    """A permanency of a barman, on a counter.

    This aims at storing a traceability of who was barman where and when.
    Mainly for ~~dick size contest~~ establishing the top 10 barmen of the semester.
    """

    user = models.ForeignKey(
        User,
        related_name="permanencies",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    counter = models.ForeignKey(
        Counter,
        related_name="permanencies",
        verbose_name=_("counter"),
        on_delete=models.CASCADE,
    )
    start = models.DateTimeField(_("start date"))
    end = models.DateTimeField(_("end date"), null=True, db_index=True)
    activity = models.DateTimeField(_("last activity date"), auto_now=True)

    class Meta:
        verbose_name = _("permanency")

    def __str__(self):
        return "%s in %s from %s (last activity: %s) to %s" % (
            self.user,
            self.counter,
            self.start.strftime("%Y-%m-%d %H:%M:%S"),
            self.activity.strftime("%Y-%m-%d %H:%M:%S"),
            self.end.strftime("%Y-%m-%d %H:%M:%S") if self.end else "",
        )

    @property
    def duration(self):
        if self.end is None:
            return self.activity - self.start
        return self.end - self.start


class CashRegisterSummary(models.Model):
    user = models.ForeignKey(
        User,
        related_name="cash_summaries",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    counter = models.ForeignKey(
        Counter,
        related_name="cash_summaries",
        verbose_name=_("counter"),
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(_("date"))
    comment = models.TextField(_("comment"), null=True, blank=True)
    emptied = models.BooleanField(_("emptied"), default=False)

    class Meta:
        verbose_name = _("cash register summary")

    def __str__(self):
        return "At %s by %s - Total: %s €" % (self.counter, self.user, self.get_total())

    def __getattribute__(self, name):
        if name[:5] == "check":
            checks = self.items.filter(is_check=True).order_by("value").all()
        if name == "ten_cents":
            return self.items.filter(value=0.1, is_check=False).first()
        elif name == "twenty_cents":
            return self.items.filter(value=0.2, is_check=False).first()
        elif name == "fifty_cents":
            return self.items.filter(value=0.5, is_check=False).first()
        elif name == "one_euro":
            return self.items.filter(value=1, is_check=False).first()
        elif name == "two_euros":
            return self.items.filter(value=2, is_check=False).first()
        elif name == "five_euros":
            return self.items.filter(value=5, is_check=False).first()
        elif name == "ten_euros":
            return self.items.filter(value=10, is_check=False).first()
        elif name == "twenty_euros":
            return self.items.filter(value=20, is_check=False).first()
        elif name == "fifty_euros":
            return self.items.filter(value=50, is_check=False).first()
        elif name == "hundred_euros":
            return self.items.filter(value=100, is_check=False).first()
        elif name == "check_1":
            return checks[0] if len(checks) > 0 else None
        elif name == "check_2":
            return checks[1] if len(checks) > 1 else None
        elif name == "check_3":
            return checks[2] if len(checks) > 2 else None
        elif name == "check_4":
            return checks[3] if len(checks) > 3 else None
        elif name == "check_5":
            return checks[4] if len(checks) > 4 else None
        else:
            return object.__getattribute__(self, name)

    def save(self, *args, **kwargs):
        if not self.id:
            self.date = timezone.now()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("counter:cash_summary_list")

    def is_owned_by(self, user):
        """Method to see if that object can be edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)

    def get_total(self):
        t = 0
        for it in self.items.all():
            t += it.quantity * it.value
        return t


class CashRegisterSummaryItem(models.Model):
    cash_summary = models.ForeignKey(
        CashRegisterSummary,
        related_name="items",
        verbose_name=_("cash summary"),
        on_delete=models.CASCADE,
    )
    value = CurrencyField(_("value"))
    quantity = models.IntegerField(_("quantity"), default=0)
    is_check = models.BooleanField(
        _("check"),
        default=False,
        help_text=_("True if this is a bank check, else False"),
    )

    class Meta:
        verbose_name = _("cash register summary item")

    def __str__(self):
        return str(self.value)


class Eticket(models.Model):
    """Eticket can be linked to a product an allows PDF generation."""

    product = models.OneToOneField(
        Product,
        related_name="eticket",
        verbose_name=_("product"),
        on_delete=models.CASCADE,
    )
    banner = models.ImageField(
        upload_to="etickets", null=True, blank=True, verbose_name=_("banner")
    )
    event_date = models.DateField(_("event date"), null=True, blank=True)
    event_title = models.CharField(
        _("event title"), max_length=64, null=True, blank=True
    )
    secret = models.CharField(_("secret"), max_length=64, unique=True)

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.secret = base64.b64encode(os.urandom(32))
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("counter:eticket_list")

    def is_owned_by(self, user):
        """Method to see if that object can be edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)

    def get_hash(self, string):
        import hashlib
        import hmac

        return hmac.new(
            bytes(self.secret, "utf-8"), bytes(string, "utf-8"), hashlib.sha1
        ).hexdigest()


class StudentCard(models.Model):
    """Alternative way to connect a customer into a counter.

    We are using Mifare DESFire EV1 specs since it's used for izly cards
    https://www.nxp.com/docs/en/application-note/AN10927.pdf
    UID is 7 byte long that means 14 hexa characters.
    """

    UID_SIZE = 14

    uid = models.CharField(
        _("uid"), max_length=UID_SIZE, unique=True, validators=[MinLengthValidator(4)]
    )
    customer = models.OneToOneField(
        Customer,
        related_name="student_card",
        verbose_name=_("student card"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("student card")
        verbose_name_plural = _("student cards")

    def __str__(self):
        return self.uid

    @staticmethod
    def is_valid(uid: str) -> bool:
        return (
            (uid.isupper() or uid.isnumeric())
            and len(uid) == StudentCard.UID_SIZE
            and not StudentCard.objects.filter(uid=uid).exists()
        )

    @staticmethod
    def can_create(customer, user):
        return user.pk == customer.user.pk or user.is_board_member or user.is_root

    def can_be_edited_by(self, obj):
        if isinstance(obj, User):
            return StudentCard.can_create(self.customer, obj)
        return False


class ReturnableProductQuerySet(models.QuerySet):
    def annotate_balance_for(self, customer: Customer):
        return self.annotate(
            balance=Coalesce(
                Subquery(
                    ReturnableProductBalance.objects.filter(
                        returnable=OuterRef("pk"), customer=customer
                    ).values("balance")
                ),
                0,
            )
        )


class ReturnableProduct(models.Model):
    """A returnable relation between two products (*consigne/déconsigne*)."""

    product = models.OneToOneField(
        to=Product,
        on_delete=models.CASCADE,
        related_name="cons",
        verbose_name=_("returnable product"),
    )
    returned_product = models.OneToOneField(
        to=Product,
        on_delete=models.CASCADE,
        related_name="dcons",
        verbose_name=_("returned product"),
    )
    max_return = models.PositiveSmallIntegerField(
        _("maximum returns"),
        default=0,
        help_text=_(
            "The maximum number of items a customer can return "
            "without having actually bought them."
        ),
    )

    objects = ReturnableProductQuerySet.as_manager()

    class Meta:
        verbose_name = _("returnable product")
        verbose_name_plural = _("returnable products")
        constraints = [
            models.CheckConstraint(
                check=~Q(product=F("returned_product")),
                name="returnableproduct_product_different_from_returned",
                violation_error_message=_(
                    "The returnable product cannot be the same as the returned one"
                ),
            )
        ]

    def __str__(self):
        return f"returnable product ({self.product_id} -> {self.returned_product_id})"

    def update_balances(self):
        """Update all returnable balances linked to this object.

        Call this when a ReturnableProduct is created or updated.

        Warning:
            This function is expensive (around a few seconds),
            so try not to run it outside a management command
            or a task.
        """

        def product_balance_subquery(product_id: int):
            return Subquery(
                Selling.objects.filter(customer=OuterRef("pk"), product_id=product_id)
                .values("customer")
                .annotate(res=Sum("quantity"))
                .values("res")
            )

        old_balance_subquery = Subquery(
            ReturnableProductBalance.objects.filter(
                customer=OuterRef("pk"), returnable=self
            ).values("balance")
        )
        new_balances = (
            Customer.objects.annotate(
                nb_cons=Coalesce(product_balance_subquery(self.product_id), 0),
                nb_dcons=Coalesce(
                    product_balance_subquery(self.returned_product_id), 0
                ),
            )
            .annotate(new_balance=F("nb_cons") - F("nb_dcons"))
            .exclude(new_balance=Coalesce(old_balance_subquery, 0))
            .values("pk", "new_balance")
        )
        updates = [
            ReturnableProductBalance(
                customer_id=c["pk"], returnable=self, balance=c["new_balance"]
            )
            for c in new_balances
        ]
        ReturnableProductBalance.objects.bulk_create(
            updates,
            update_conflicts=True,
            update_fields=["balance"],
            unique_fields=["customer_id", "returnable"],
        )


class ReturnableProductBalance(models.Model):
    """The returnable products balances of a customer"""

    customer = models.ForeignKey(
        to=Customer, on_delete=models.CASCADE, related_name="return_balances"
    )
    returnable = models.ForeignKey(
        to=ReturnableProduct, on_delete=models.CASCADE, related_name="balances"
    )
    balance = models.SmallIntegerField(blank=True, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "returnable"],
                name="returnable_product_unique_type_per_customer",
            )
        ]

    def __str__(self):
        return (
            f"return balance of {self.customer} "
            f"for {self.returnable.product_id} : {self.balance}"
        )
