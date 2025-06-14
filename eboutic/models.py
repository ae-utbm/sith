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
from typing import Any, Self

from dict2xml import dict2xml
from django.conf import settings
from django.db import DataError, models
from django.db.models import F, OuterRef, Subquery, Sum
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from core.models import User
from counter.fields import CurrencyField
from counter.models import (
    BillingInfo,
    Counter,
    Customer,
    Product,
    Refilling,
    Selling,
    get_eboutic,
)


def get_eboutic_products(user: User) -> list[Product]:
    products = (
        get_eboutic()
        .products.filter(product_type__isnull=False)
        .filter(archived=False)
        .filter(limit_age__lte=user.age)
        .annotate(order=F("product_type__order"))
        .annotate(category=F("product_type__name"))
        .annotate(category_comment=F("product_type__comment"))
        .annotate(price=F("selling_price"))  # <-- selected price for basket validation
        .prefetch_related("buying_groups")  # <-- used in `Product.can_be_sold_to`
    )
    return [p for p in products if p.can_be_sold_to(user)]


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

    def can_be_viewed_by(self, user):
        return self.user == user

    @cached_property
    def contains_refilling_item(self) -> bool:
        return self.items.filter(
            type_id=settings.SITH_COUNTER_PRODUCTTYPE_REFILLING
        ).exists()

    @cached_property
    def total(self) -> float:
        return float(
            self.items.aggregate(
                total=Sum(F("quantity") * F("product_unit_price"), default=0)
            )["total"]
        )

    def generate_sales(self, counter, seller: User, payment_method: str):
        """Generate a list of sold items corresponding to the items
        of this basket WITHOUT saving them NOR deleting the basket.

        Example:
            ```python
            counter = Counter.objects.get(name="Eboutic")
            sales = basket.generate_sales(counter, "SITH_ACCOUNT")
            # here the basket is in the same state as before the method call

            with transaction.atomic():
                for sale in sales:
                    sale.save()
                basket.delete()
                # all the basket items are deleted by the on_delete=CASCADE relation
                # thus only the sales remain
            ```
        """
        # I must proceed with two distinct requests instead of
        # only one with a join because the AbstractBaseItem model has been
        # poorly designed. If you refactor the model, please refactor this too.
        items = self.items.order_by("product_id")
        ids = [item.product_id for item in items]
        products = Product.objects.filter(id__in=ids).order_by("id")
        # items and products are sorted in the same order
        sales = []
        for item, product in zip(items, products, strict=False):
            sales.append(
                Selling(
                    label=product.name,
                    counter=counter,
                    club=product.club,
                    product=product,
                    seller=seller,
                    customer=Customer.get_or_create(self.user)[0],
                    unit_price=item.product_unit_price,
                    quantity=item.quantity,
                    payment_method=payment_method,
                )
            )
        return sales

    def get_e_transaction_data(self) -> list[tuple[str, Any]]:
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

        The total amount is the sum of (product_unit_price * quantity)
        for all items related to the invoice.
        """
        # aggregates within subqueries require a little bit of black magic,
        # but hopefully, django gives a comprehensive documentation for that :
        # https://docs.djangoproject.com/en/stable/ref/models/expressions/#using-aggregates-within-a-subquery-expression
        return self.annotate(
            total=Subquery(
                InvoiceItem.objects.filter(invoice_id=OuterRef("pk"))
                .values("invoice_id")
                .annotate(total=Sum(F("product_unit_price") * F("quantity")))
                .values("total")
            )
        )


class Invoice(models.Model):
    """Invoices are generated once the payment has been validated."""

    user = models.ForeignKey(
        User,
        related_name="invoices",
        verbose_name=_("user"),
        blank=False,
        on_delete=models.CASCADE,
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
        customer, created = Customer.get_or_create(user=self.user)
        eboutic = Counter.objects.filter(type="EBOUTIC").first()
        for i in self.items.all():
            if i.type_id == settings.SITH_COUNTER_PRODUCTTYPE_REFILLING:
                new = Refilling(
                    counter=eboutic,
                    customer=customer,
                    operator=self.user,
                    amount=i.product_unit_price * i.quantity,
                    payment_method="CARD",
                    bank="OTHER",
                    date=self.date,
                )
                new.save()
            else:
                product = Product.objects.filter(id=i.product_id).first()
                new = Selling(
                    label=i.product_name,
                    counter=eboutic,
                    club=product.club,
                    product=product,
                    seller=self.user,
                    customer=customer,
                    unit_price=i.product_unit_price,
                    quantity=i.quantity,
                    payment_method="CARD",
                    is_validated=True,
                    date=self.date,
                )
                new.save()
        self.validated = True
        self.save()


class AbstractBaseItem(models.Model):
    product_id = models.IntegerField(_("product id"))
    product_name = models.CharField(_("product name"), max_length=255)
    type_id = models.IntegerField(_("product type id"))
    product_unit_price = CurrencyField(_("unit price"))
    quantity = models.PositiveIntegerField(_("quantity"))

    class Meta:
        abstract = True

    def __str__(self):
        return "Item: %s (%s) x%d" % (
            self.product_name,
            self.product_unit_price,
            self.quantity,
        )


class BasketItem(AbstractBaseItem):
    basket = models.ForeignKey(
        Basket, related_name="items", verbose_name=_("basket"), on_delete=models.CASCADE
    )

    @classmethod
    def from_product(cls, product: Product, quantity: int, basket: Basket):
        """Create a BasketItem with the same characteristics as the
        product passed in parameters, with the specified quantity.

        Warning:
            the basket field is not filled, so you must set
            it yourself before saving the model.
        """
        return cls(
            basket=basket,
            product_id=product.id,
            product_name=product.name,
            type_id=product.product_type_id,
            quantity=quantity,
            product_unit_price=product.selling_price,
        )


class InvoiceItem(AbstractBaseItem):
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        verbose_name=_("invoice"),
        on_delete=models.CASCADE,
    )
