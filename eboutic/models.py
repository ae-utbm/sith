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

import hmac
from datetime import datetime
from enum import Enum
from typing import Self

from dict2xml import dict2xml
from django.conf import settings
from django.db import DataError, models
from django.db.models import F, OuterRef, Q, Subquery, Sum
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from core.models import User
from counter.fields import CurrencyField
from counter.models import (
    BillingInfo,
    Customer,
    Price,
    Product,
    Refilling,
    Selling,
    get_eboutic,
)


def get_eboutic_prices(user: User) -> list[Price]:
    return list(
        Price.objects.filter(
            Q(is_always_shown=True, groups__in=user.all_groups)
            | Q(
                id=Subquery(
                    Price.objects.filter(
                        product_id=OuterRef("product_id"), groups__in=user.all_groups
                    )
                    .order_by("amount")
                    .values("id")[:1]
                )
            ),
            product__product_type__isnull=False,
            product__archived=False,
            product__limit_age__lte=user.age,
            product__counters=get_eboutic(),
        )
        .select_related("product", "product__product_type")
        .order_by("product__product_type__order", "product_id", "amount")
        .distinct()
    )


class BillingInfoState(Enum):
    VALID = 1
    EMPTY = 2
    MISSING_PHONE_NUMBER = 3

    @classmethod
    def from_model(cls, info: BillingInfo | None) -> BillingInfoState:
        if info is None:
            return cls.EMPTY
        for attr in [
            "first_name",
            "last_name",
            "address_1",
            "zip_code",
            "city",
            "country",
        ]:
            if getattr(info, attr) == "":
                return cls.EMPTY
        if info.phone_number is None:
            return cls.MISSING_PHONE_NUMBER
        return cls.VALID


class Basket(models.Model):
    """Basket is built when the user connects to an eboutic page."""

    user = models.ForeignKey(
        User,
        related_name="baskets",
        verbose_name=_("user"),
        blank=False,
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(_("date"), auto_now=True)

    def __str__(self):
        return f"{self.user}'s basket ({self.items.all().count()} items)"

    def can_be_viewed_by(self, user: User):
        return self.user == user

    @cached_property
    def contains_refilling_item(self) -> bool:
        return self.items.filter(
            product__product_type_id=settings.SITH_COUNTER_PRODUCTTYPE_REFILLING
        ).exists()

    @cached_property
    def total(self) -> float:
        return float(
            self.items.aggregate(total=Sum(F("quantity") * F("unit_price"), default=0))[
                "total"
            ]
        )

    def generate_sales(
        self, counter, seller: User, payment_method: Selling.PaymentMethod
    ):
        """Generate a list of sold items corresponding to the items
        of this basket WITHOUT saving them NOR deleting the basket.

        Example:
            ```python
            counter = Counter.objects.get(name="Eboutic")
            user = User.objects.get(username="bibou")
            sales = basket.generate_sales(counter, user, Selling.PaymentMethod.SITH_ACCOUNT)
            # here the basket is in the same state as before the method call

            with transaction.atomic():
                for sale in sales:
                    sale.save()
                basket.delete()
                # all the basket items are deleted by the on_delete=CASCADE relation
                # thus only the sales remain
            ```
        """
        customer = Customer.get_or_create(self.user)[0]
        return [
            Selling(
                label=item.label,
                counter=counter,
                club_id=item.product.club_id,
                product=item.product,
                seller=seller,
                customer=customer,
                unit_price=item.unit_price,
                quantity=item.quantity,
                payment_method=payment_method,
            )
            for item in self.items.select_related("product")
        ]

    def get_e_transaction_data(self) -> list[tuple[str, str]]:
        user = self.user
        if not hasattr(user, "customer"):
            raise Customer.DoesNotExist
        customer = user.customer
        if (
            not hasattr(user.customer, "billing_infos")
            or BillingInfoState.from_model(user.customer.billing_infos)
            != BillingInfoState.VALID
        ):
            raise BillingInfo.DoesNotExist
        cart = {
            "shoppingcart": {"total": {"totalQuantity": min(self.items.count(), 99)}}
        }
        cart = '<?xml version="1.0" encoding="UTF-8" ?>' + dict2xml(
            cart, newlines=False
        )
        data = [
            ("PBX_SITE", settings.SITH_EBOUTIC_PBX_SITE),
            ("PBX_RANG", settings.SITH_EBOUTIC_PBX_RANG),
            ("PBX_IDENTIFIANT", settings.SITH_EBOUTIC_PBX_IDENTIFIANT),
            ("PBX_TOTAL", str(int(self.total * 100))),
            ("PBX_DEVISE", "978"),  # This is Euro
            ("PBX_CMD", str(self.id)),
            ("PBX_PORTEUR", user.email),
            ("PBX_RETOUR", "Amount:M;BasketID:R;Auto:A;Error:E;Sig:K"),
            ("PBX_HASH", "SHA512"),
            ("PBX_TYPEPAIEMENT", "CARTE"),
            ("PBX_TYPECARTE", "CB"),
            ("PBX_TIME", datetime.now().replace(microsecond=0).isoformat("T")),
            ("PBX_SHOPPINGCART", cart),
            ("PBX_BILLING", customer.billing_infos.to_3dsv2_xml()),
        ]
        pbx_hmac = hmac.new(
            settings.SITH_EBOUTIC_HMAC_KEY,
            bytes("&".join("=".join(d) for d in data), "utf-8"),
            "sha512",
        )
        data.append(("PBX_HMAC", pbx_hmac.hexdigest().upper()))
        return data


class InvoiceQueryset(models.QuerySet):
    def annotate_total(self) -> Self:
        """Annotate the queryset with the total amount of each invoice.

        The total amount is the sum of (unit_price * quantity)
        for all items related to the invoice.
        """
        # aggregates within subqueries require a little bit of black magic,
        # but hopefully, django gives a comprehensive documentation for that :
        # https://docs.djangoproject.com/en/stable/ref/models/expressions/#using-aggregates-within-a-subquery-expression
        return self.annotate(
            total=Subquery(
                InvoiceItem.objects.filter(invoice_id=OuterRef("pk"))
                .values("invoice_id")
                .annotate(total=Sum(F("unit_price") * F("quantity")))
                .values("total")
            )
        )


class Invoice(models.Model):
    """Invoices are generated once the payment has been validated."""

    user = models.ForeignKey(
        User, related_name="invoices", verbose_name=_("user"), on_delete=models.CASCADE
    )
    date = models.DateTimeField(_("date"), auto_now=True)
    validated = models.BooleanField(_("validated"), default=False)

    objects = InvoiceQueryset.as_manager()

    def __str__(self):
        return f"{self.user} - {self.get_total()} - {self.date}"

    def get_total(self) -> float:
        return float(
            self.items.aggregate(
                total=Sum(F("quantity") * F("product_unit_price"), default=0)
            )["total"]
        )

    def validate(self):
        if self.validated:
            raise DataError(_("Invoice already validated"))
        customer, _created = Customer.get_or_create(user=self.user)
        kwargs = {
            "counter": get_eboutic(),
            "customer": customer,
            "date": self.date,
            "payment_method": Selling.PaymentMethod.CARD,
        }
        for i in self.items.select_related("product"):
            if i.product.product_type_id == settings.SITH_COUNTER_PRODUCTTYPE_REFILLING:
                Refilling.objects.create(
                    **kwargs, operator=self.user, amount=i.unit_price * i.quantity
                )
            else:
                Selling.objects.create(
                    **kwargs,
                    label=i.label,
                    club_id=i.product.club_id,
                    product=i.product,
                    seller=self.user,
                    unit_price=i.unit_price,
                    quantity=i.quantity,
                )
        self.validated = True
        self.save()


class AbstractBaseItem(models.Model):
    product = models.ForeignKey(
        Product, verbose_name=_("product"), on_delete=models.PROTECT
    )
    label = models.CharField(_("product name"), max_length=255)
    unit_price = CurrencyField(_("unit price"))
    quantity = models.PositiveIntegerField(_("quantity"))

    class Meta:
        abstract = True

    def __str__(self):
        return "Item: %s (%s) x%d" % (self.product.name, self.unit_price, self.quantity)


class BasketItem(AbstractBaseItem):
    basket = models.ForeignKey(
        Basket, related_name="items", verbose_name=_("basket"), on_delete=models.CASCADE
    )

    @classmethod
    def from_price(cls, price: Price, quantity: int, basket: Basket):
        """Create a BasketItem with the same characteristics as the
        product price passed in parameters, with the specified quantity.
        """
        return cls(
            basket=basket,
            label=price.full_label,
            product_id=price.product_id,
            quantity=quantity,
            unit_price=price.amount,
        )


class InvoiceItem(AbstractBaseItem):
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        verbose_name=_("invoice"),
        on_delete=models.CASCADE,
    )
