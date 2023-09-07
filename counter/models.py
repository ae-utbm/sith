# -*- coding:utf-8 -*
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
from __future__ import annotations

from typing import Tuple

from django.db import models
from django.db.models import F, Value, Sum, QuerySet, OuterRef, Exists
from django.db.models.functions import Concat, Length
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.forms import ValidationError
from django.utils.functional import cached_property

from datetime import timedelta, date, datetime
import random
import string
import os
import base64
from dict2xml import dict2xml

from core.utils import get_start_of_semester
from sith.settings import SITH_COUNTER_OFFICES, SITH_MAIN_CLUB
from club.models import Club, Membership
from accounting.models import CurrencyField
from core.models import Group, User, Notification
from subscription.models import Subscription

from django_countries.fields import CountryField


class Customer(models.Model):
    """
    This class extends a user to make a customer. It adds some basic customers' information, such as the account ID, and
    is used by other accounting classes as reference to the customer, rather than using User
    """

    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    account_id = models.CharField(_("account id"), max_length=10, unique=True)
    amount = CurrencyField(_("amount"), default=0)
    recorded_products = models.IntegerField(_("recorded product"), default=0)

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customers")
        ordering = ["account_id"]

    def __str__(self):
        return "%s - %s" % (self.user.username, self.account_id)

    @property
    def can_record(self):
        return self.recorded_products > -settings.SITH_ECOCUP_LIMIT

    def can_record_more(self, number):
        return self.recorded_products - number >= -settings.SITH_ECOCUP_LIMIT

    @property
    def can_buy(self) -> bool:
        """
        Check if whether this customer has the right to
        purchase any item.
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
    def get_or_create(cls, user: User) -> Tuple[Customer, bool]:
        """
        Work in pretty much the same way as the usual get_or_create method,
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

    def save(self, allow_negative=False, is_selling=False, *args, **kwargs):
        """
        is_selling : tell if the current action is a selling
        allow_negative : ignored if not a selling. Allow a selling to put the account in negative
        Those two parameters avoid blocking the save method of a customer if his account is negative
        """
        if self.amount < 0 and (is_selling and not allow_negative):
            raise ValidationError(_("Not enough money"))
        super(Customer, self).save(*args, **kwargs)

    def recompute_amount(self):
        refillings = self.refillings.aggregate(sum=Sum(F("amount")))["sum"]
        self.amount = refillings if refillings is not None else 0
        purchases = (
            self.buyings.filter(payment_method="SITH_ACCOUNT")
            .annotate(amount=F("quantity") * F("unit_price"))
            .aggregate(sum=Sum(F("amount")))
        )["sum"]
        if purchases is not None:
            self.amount -= purchases
        self.save()

    def get_absolute_url(self):
        return reverse("core:user_account", kwargs={"user_id": self.user.pk})

    def get_full_url(self):
        return "".join(["https://", settings.SITH_URL, self.get_absolute_url()])


class BillingInfo(models.Model):
    """
    Represent the billing information of a user, which are required
    by the 3D-Secure v2 system used by the etransaction module
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

    def to_3dsv2_xml(self) -> str:
        """
        Convert the data from this model into a xml usable
        by the online paying service of the Crédit Agricole bank.
        see : `https://www.ca-moncommerce.com/espace-client-mon-commerce/up2pay-e-transactions/ma-documentation/manuel-dintegration-focus-3ds-v2/principes-generaux/#integration-3dsv2-developpeur-webmaster`
        """
        data = {
            "Address": {
                "FirstName": self.first_name,
                "LastName": self.last_name,
                "Address1": self.address_1,
                "ZipCode": self.zip_code,
                "City": self.city,
                "CountryCode": self.country.numeric,  # ISO-3166-1 numeric code
            }
        }
        if self.address_2:
            data["Address"]["Address2"] = self.address_2
        xml = dict2xml(data, wrap="Billing", newlines=False)
        return '<?xml version="1.0" encoding="UTF-8" ?>' + xml

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ProductType(models.Model):
    """
    This describes a product type
    Useful only for categorizing, changes are made at the product level for now
    """

    name = models.CharField(_("name"), max_length=30)
    description = models.TextField(_("description"), null=True, blank=True)
    comment = models.TextField(_("comment"), null=True, blank=True)
    icon = models.ImageField(upload_to="products", null=True, blank=True)

    # priority holds no real backend logic but helps to handle the order in which
    # the items are to be shown to the user
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("product type")
        ordering = ["-priority", "name"]

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_anonymous:
            return False
        if user.is_in_group(pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
            return True
        return False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("counter:producttype_list")


class Product(models.Model):
    """
    This describes a product, with all its related informations
    """

    name = models.CharField(_("name"), max_length=64)
    description = models.TextField(_("description"), blank=True)
    product_type = models.ForeignKey(
        ProductType,
        related_name="products",
        verbose_name=_("product type"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    code = models.CharField(_("code"), max_length=16, blank=True)
    purchase_price = CurrencyField(_("purchase price"))
    selling_price = CurrencyField(_("selling price"))
    special_selling_price = CurrencyField(_("special selling price"))
    icon = models.ImageField(
        upload_to="products", null=True, blank=True, verbose_name=_("icon")
    )
    club = models.ForeignKey(
        Club, related_name="products", verbose_name=_("club"), on_delete=models.CASCADE
    )
    limit_age = models.IntegerField(_("limit age"), default=0)
    tray = models.BooleanField(_("tray price"), default=False)
    parent_product = models.ForeignKey(
        "self",
        related_name="children_products",
        verbose_name=_("parent product"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    buying_groups = models.ManyToManyField(
        Group, related_name="products", verbose_name=_("buying groups"), blank=True
    )
    archived = models.BooleanField(_("archived"), default=False)

    class Meta:
        verbose_name = _("product")

    @property
    def is_record_product(self):
        return settings.SITH_ECOCUP_CONS == self.id

    @property
    def is_unrecord_product(self):
        return settings.SITH_ECOCUP_DECO == self.id

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_anonymous:
            return False
        if user.is_in_group(
            pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID
        ) or user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID):
            return True
        return False

    def get_absolute_url(self):
        return reverse("counter:product_list")

    def can_be_sold_to(self, user: User) -> bool:
        """
        Check if whether the user given in parameter has the right to buy
        this product or not.

        This must be not confused with the Customer.can_buy()
        method as the present method returns an information
        about the relation between a User and a Product,
        whereas the other tells something about a Customer
        (and not a user, they are not the same model).

        :return: True if the user can buy this product else False
        """
        if not self.buying_groups.exists():
            return True
        for group_id in self.buying_groups.values_list("pk", flat=True):
            if user.is_in_group(pk=group_id):
                return True
        return False

    @property
    def profit(self):
        return self.selling_price - self.purchase_price

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class CounterQuerySet(models.QuerySet):
    def annotate_has_barman(self, user: User) -> CounterQuerySet:
        """
        Annotate the queryset with the `user_is_barman` field.
        For each counter, this field has value True if the user
        is a barman of this counter, else False.

        :param user: the user we want to check if he is a barman

        Example::

            sli = User.objects.get(username="sli")
            counters = (
                Counter.objects
                .annotate_has_barman(sli)  # add the user_has_barman boolean field
                .filter(has_annotated_barman=True)  # keep only counters where this user is barman
            )
            print("Sli est barman dans les comptoirs suivants :")
            for counter in counters:
                print(f"- {counter.name}")
        """
        subquery = user.counters.filter(pk=OuterRef("pk"))
        # noinspection PyTypeChecker
        return self.annotate(has_annotated_barman=Exists(subquery))


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

    def __getattribute__(self, name):
        if name == "edit_groups":
            return Group.objects.filter(
                name=self.club.unix_name + settings.SITH_BOARD_SUFFIX
            ).all()
        return object.__getattribute__(self, name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.type == "EBOUTIC":
            return reverse("eboutic:main")
        return reverse("counter:details", kwargs={"counter_id": self.id})

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        mem = self.club.get_membership_for(user)
        if mem and mem.role >= 7:
            return True
        return user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID)

    def can_be_viewed_by(self, user):
        if self.type == "BAR":
            return True
        return user.is_board_member or user in self.sellers.all()

    def gen_token(self):
        """Generate a new token for this counter"""
        self.token = "".join(
            random.choice(string.ascii_letters + string.digits) for x in range(30)
        )
        self.save()

    def add_barman(self, user):
        """
        Logs a barman in to the given counter
        A user is stored as a tuple with its login time
        """
        Permanency(user=user, counter=self, start=timezone.now(), end=None).save()

    def del_barman(self, user):
        """
        Logs a barman out and store its permanency
        """
        perm = Permanency.objects.filter(counter=self, user=user, end=None).all()
        for p in perm:
            p.end = p.activity
            p.save()

    @cached_property
    def barmen_list(self):
        return self.get_barmen_list()

    def get_barmen_list(self):
        """
        Returns the barman list as list of User

        Also handle the timeout of the barmen
        """
        pl = Permanency.objects.filter(counter=self, end=None).all()
        bl = []
        for p in pl:
            if timezone.now() - p.activity < timedelta(
                minutes=settings.SITH_BARMAN_TIMEOUT
            ):
                bl.append(p.user)
            else:
                p.end = p.activity
                p.save()
        return bl

    def get_random_barman(self):
        """
        Return a random user being currently a barman
        """
        bl = self.get_barmen_list()
        return bl[random.randrange(0, len(bl))]

    def update_activity(self):
        """
        Update the barman activity to prevent timeout
        """
        for p in Permanency.objects.filter(counter=self, end=None).all():
            p.save()  # Update activity

    def is_open(self):
        return len(self.barmen_list) > 0

    def is_inactive(self):
        """
        Returns True if the counter self is inactive from SITH_COUNTER_MINUTE_INACTIVE's value minutes, else False
        """
        return self.is_open() and (
            (timezone.now() - self.permanencies.order_by("-activity").first().activity)
            > timedelta(minutes=settings.SITH_COUNTER_MINUTE_INACTIVE)
        )

    def barman_list(self):
        """
        Returns the barman id list
        """
        return [b.id for b in self.get_barmen_list()]

    def can_refill(self):
        """
        Show if the counter authorize the refilling with physic money
        """

        if self.type != "BAR":
            return False
        if self.id in SITH_COUNTER_OFFICES:
            # If the counter is either 'AE' or 'BdF', refills are authorized
            return True
        is_ae_member = False
        ae = Club.objects.get(unix_name=SITH_MAIN_CLUB["unix_name"])
        for barman in self.get_barmen_list():
            if ae.get_membership_for(barman):
                is_ae_member = True
        return is_ae_member

    def get_top_barmen(self) -> QuerySet:
        """
        Return a QuerySet querying the office hours stats of all the barmen of all time
        of this counter, ordered by descending number of hours.

        Each element of the QuerySet corresponds to a barman and has the following data :
            - the full name (first name + last name) of the barman
            - the nickname of the barman
            - the promo of the barman
            - the total number of office hours the barman did attend
        """
        return (
            self.permanencies.exclude(end=None)
            .annotate(
                name=Concat(F("user__first_name"), Value(" "), F("user__last_name"))
            )
            .annotate(nickname=F("user__nick_name"))
            .annotate(promo=F("user__promo"))
            .values("user", "name", "nickname", "promo")
            .annotate(perm_sum=Sum(F("end") - F("start")))
            .exclude(perm_sum=None)
            .order_by("-perm_sum")
        )

    def get_top_customers(self, since=get_start_of_semester()) -> QuerySet:
        """
        Return a QuerySet querying the money spent by customers of this counter
        since the specified date, ordered by descending amount of money spent.

        Each element of the QuerySet corresponds to a customer and has the following data :
            - the full name (first name + last name) of the customer
            - the nickname of the customer
            - the amount of money spent by the customer
        """
        return (
            self.sellings.filter(date__gte=since)
            .annotate(
                name=Concat(
                    F("customer__user__first_name"),
                    Value(" "),
                    F("customer__user__last_name"),
                )
            )
            .annotate(nickname=F("customer__user__nick_name"))
            .annotate(promo=F("customer__user__promo"))
            .values("customer__user", "promo", "name", "nickname")
            .annotate(
                selling_sum=Sum(
                    F("unit_price") * F("quantity"), output_field=CurrencyField()
                )
            )
            .filter(selling_sum__gt=0)
            .order_by("-selling_sum")
        )

    def get_total_sales(self, since=get_start_of_semester()) -> CurrencyField:
        """
        Compute and return the total turnover of this counter
        since the date specified in parameter (by default, since the start of the current
        semester)
        :param since: timestamp from which to perform the calculation
        :type since: datetime | date
        :return: Total revenue earned at this counter
        """
        if isinstance(since, date):
            since = datetime.combine(since, datetime.min.time())
        total = self.sellings.filter(date__gte=since).aggregate(
            total=Sum(F("quantity") * F("unit_price"), output_field=CurrencyField())
        )["total"]
        return total if total is not None else CurrencyField(0)


class Refilling(models.Model):
    """
    Handle the refilling
    """

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
        choices=settings.SITH_COUNTER_PAYMENT_METHOD,
        default="CASH",
    )
    bank = models.CharField(
        _("bank"), max_length=255, choices=settings.SITH_COUNTER_BANK, default="OTHER"
    )
    is_validated = models.BooleanField(_("is validated"), default=False)

    class Meta:
        verbose_name = _("refilling")

    def __str__(self):
        return "Refilling: %.2f for %s" % (
            self.amount,
            self.customer.user.get_display_name(),
        )

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_owner(self.counter) and self.payment_method != "CARD"

    def delete(self, *args, **kwargs):
        self.customer.amount -= self.amount
        self.customer.save()
        super(Refilling, self).delete(*args, **kwargs)

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
        super(Refilling, self).save(*args, **kwargs)


class Selling(models.Model):
    """
    Handle the sellings
    """

    label = models.CharField(_("label"), max_length=64)
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

    class Meta:
        verbose_name = _("selling")

    def __str__(self):
        return "Selling: %d x %s (%f) for %s" % (
            self.quantity,
            self.label,
            self.quantity * self.unit_price,
            self.customer.user.get_display_name(),
        )

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_owner(self.counter) and self.payment_method != "CARD"

    def can_be_viewed_by(self, user):
        if (
            not hasattr(self, "customer") or self.customer is None
        ):  # Customer can be set to Null
            return False
        return user == self.customer.user

    def delete(self, *args, **kwargs):
        if self.payment_method == "SITH_ACCOUNT":
            self.customer.amount += self.quantity * self.unit_price
            self.customer.save()
        super(Selling, self).delete(*args, **kwargs)

    def send_mail_customer(self):
        event = self.product.eticket.event_title or _("Unknown event")
        subject = _("Eticket bought for the event %(event)s") % {"event": event}
        message_html = _(
            "You bought an eticket for the event %(event)s.\nYou can download it directly from this link %(eticket)s.\nYou can also retrieve all your e-tickets on your account page %(url)s."
        ) % {
            "event": event,
            "url": "".join(
                (
                    '<a href="',
                    self.customer.get_full_url(),
                    '">',
                    self.customer.get_full_url(),
                    "</a>",
                )
            ),
            "eticket": "".join(
                (
                    '<a href="',
                    self.get_eticket_full_url(),
                    '">',
                    self.get_eticket_full_url(),
                    "</a>",
                )
            ),
        }
        message_txt = _(
            "You bought an eticket for the event %(event)s.\nYou can download it directly from this link %(eticket)s.\nYou can also retrieve all your e-tickets on your account page %(url)s."
        ) % {
            "event": event,
            "url": self.customer.get_full_url(),
            "eticket": self.get_eticket_full_url(),
        }
        self.customer.user.email_user(subject, message_txt, html_message=message_html)

    def save(self, allow_negative=False, *args, **kwargs):
        """
        allow_negative : Allow this selling to use more money than available for this user
        """
        if not self.date:
            self.date = timezone.now()
        self.full_clean()
        if not self.is_validated:
            self.customer.amount -= self.quantity * self.unit_price
            self.customer.save(allow_negative=allow_negative, is_selling=True)
            self.is_validated = True
        u = User.objects.filter(id=self.customer.user.id).first()
        if u.was_subscribed:
            if (
                self.product
                and self.product.id == settings.SITH_PRODUCT_SUBSCRIPTION_ONE_SEMESTER
            ):
                sub = Subscription(
                    member=u,
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
                u = User.objects.filter(id=self.customer.user.id).first()
                sub = Subscription(
                    member=u,
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
        if self.customer.user.preferences.notify_on_click:
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
                param="%d x %s" % (self.quantity, self.label),
                type="SELLING",
            ).save()
        super(Selling, self).save(*args, **kwargs)
        try:
            # The product has no id until it's saved
            if self.product.eticket:
                self.send_mail_customer()
        except:
            pass

    def get_eticket_full_url(self):
        eticket_url = reverse("counter:eticket_pdf", kwargs={"selling_id": self.id})
        return "".join(["https://", settings.SITH_URL, eticket_url])


class Permanency(models.Model):
    """
    This class aims at storing a traceability of who was barman where and when
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
            checks = self.items.filter(check=True).order_by("value").all()
        if name == "ten_cents":
            return self.items.filter(value=0.1, check=False).first()
        elif name == "twenty_cents":
            return self.items.filter(value=0.2, check=False).first()
        elif name == "fifty_cents":
            return self.items.filter(value=0.5, check=False).first()
        elif name == "one_euro":
            return self.items.filter(value=1, check=False).first()
        elif name == "two_euros":
            return self.items.filter(value=2, check=False).first()
        elif name == "five_euros":
            return self.items.filter(value=5, check=False).first()
        elif name == "ten_euros":
            return self.items.filter(value=10, check=False).first()
        elif name == "twenty_euros":
            return self.items.filter(value=20, check=False).first()
        elif name == "fifty_euros":
            return self.items.filter(value=50, check=False).first()
        elif name == "hundred_euros":
            return self.items.filter(value=100, check=False).first()
        elif name == "check_1":
            return checks[0] if 0 < len(checks) else None
        elif name == "check_2":
            return checks[1] if 1 < len(checks) else None
        elif name == "check_3":
            return checks[2] if 2 < len(checks) else None
        elif name == "check_4":
            return checks[3] if 3 < len(checks) else None
        elif name == "check_5":
            return checks[4] if 4 < len(checks) else None
        else:
            return object.__getattribute__(self, name)

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_anonymous:
            return False
        if user.is_in_group(pk=settings.SITH_GROUP_COUNTER_ADMIN_ID):
            return True
        return False

    def get_total(self):
        t = 0
        for it in self.items.all():
            t += it.quantity * it.value
        return t

    def save(self, *args, **kwargs):
        if not self.id:
            self.date = timezone.now()
        return super(CashRegisterSummary, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("counter:cash_summary_list")


class CashRegisterSummaryItem(models.Model):
    cash_summary = models.ForeignKey(
        CashRegisterSummary,
        related_name="items",
        verbose_name=_("cash summary"),
        on_delete=models.CASCADE,
    )
    value = CurrencyField(_("value"))
    quantity = models.IntegerField(_("quantity"), default=0)
    check = models.BooleanField(_("check"), default=False)

    class Meta:
        verbose_name = _("cash register summary item")


class Eticket(models.Model):
    """
    Eticket can be linked to a product an allows PDF generation
    """

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
        return "%s" % (self.product.name)

    def get_absolute_url(self):
        return reverse("counter:eticket_list")

    def save(self, *args, **kwargs):
        if not self.id:
            self.secret = base64.b64encode(os.urandom(32))
        return super(Eticket, self).save(*args, **kwargs)

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
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
    """
    Alternative way to connect a customer into a counter
    We are using Mifare DESFire EV1 specs since it's used for izly cards
    https://www.nxp.com/docs/en/application-note/AN10927.pdf
    UID is 7 byte long that means 14 hexa characters
    """

    UID_SIZE = 14

    @staticmethod
    def is_valid(uid):
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

    uid = models.CharField(
        _("uid"), max_length=14, unique=True, validators=[MinLengthValidator(4)]
    )
    customer = models.ForeignKey(
        Customer,
        related_name="student_cards",
        verbose_name=_("student cards"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
