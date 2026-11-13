from django.db import models
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.models import User


class OperationType(models.IntegerChoices):
    Overwrite = 1, _("overwrite")
    Refuel = 2, _("refuel")
    TransferTo = 3, _("transfer to")
    TransferFrom = 4, _("transfer from")


class Stock(models.Model):
    name = models.CharField(_("name"), max_length=64)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now_add=True)
    club = models.ForeignKey(Club, on_delete=models.PROTECT)
    can_be_view_by_board = models.BooleanField(
        _("can be view by board members"), default=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "club"],
                name="unique_name_club",
                violation_error_message="errere",
            )
        ]

    def __str__(self):
        return self.name


class StockAction(models.Model):
    action = models.IntegerField(
        _("action type"), choices=OperationType, default=OperationType.Overwrite
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    comment = models.TextField(_("comment"), default="")
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return str(OperationType(self.action).label)


class StockItem(models.Model):
    name = models.CharField(_("name"), max_length=64)
    description = models.TextField(_("description"), default="")
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    is_hidden = models.BooleanField(_("is hidden"), default=False)
    is_allow_negative = models.BooleanField(_("can be negative"), default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="unique_item_name")
        ]

    def __str__(self):
        return self.name


class StockItemStock(models.Model):
    item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="stock_links"
    )
    stock = models.ForeignKey(
        Stock, on_delete=models.PROTECT, related_name="item_links"
    )
    quantity = models.DecimalField(
        _("quantity"), max_digits=15, decimal_places=2, default=0
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item", "stock"], name="unique_item_stock")
        ]

    def __str__(self):
        return self.item.name

    @property
    def name(self):
        return self.item.name

    @property
    def description(self):
        return self.item.description

    @property
    def is_hidden(self):
        return self.item.is_hidden

    @property
    def is_allow_negative(self):
        return self.item.is_allow_negative

    @property
    def last_known_quantity(self):
        return self.quantity


class StockItemAction(models.Model):
    quantity_before = models.DecimalField(
        _("quantity before"), max_digits=15, decimal_places=2, default=0
    )
    quantity_after = models.DecimalField(
        _("quantity after"), max_digits=15, decimal_places=2, default=0
    )
    action = models.ForeignKey(StockAction, on_delete=models.PROTECT)
    item = models.ForeignKey(StockItemStock, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.quantity_after - self.quantity_before)


class LinkedModel(models.Model):
    class Meta:
        abstract = True

    def link(self, **ids):
        for name, pk in ids.items():
            field = self._meta.get_field(name)
            if not (field.many_to_one or field.one_to_one) or not field.concrete:
                raise ValueError(f"{name} is not a forward FK/OneToOne")
            setattr(self, field.attname, pk)


class StockItemActionMetadataBase(LinkedModel):
    item_action = models.OneToOneField(
        StockItemAction,
        on_delete=models.PROTECT,
        related_name="%(class)s_metadata",
    )

    class Meta:
        abstract = True

    def set_relations(self, item_action_pk, **ids):
        self.item_action_id = item_action_pk
        return super().link(**ids)


class StockRefuelMetadata(StockItemActionMetadataBase):
    unit_price = models.DecimalField(_("unit price"), max_digits=20, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unit_price__gt=0), name="unit_price_gt_0"
            )
        ]

    def __str__(self):
        return _("refuel with unit price %s") % self.unit_price

    @property
    def added_quantity(self):
        if hasattr(self, "_added_quantity"):
            return self._added_quantity
        return self.item_action.quantity_after - self.item_action.quantity_before

    @added_quantity.setter
    def added_quantity(self, value):
        self._added_quantity = value

    @added_quantity.deleter
    def added_quantity(self):
        self.__dict__.pop("_added_quantity", None)


class StockTransferMetadata(StockItemActionMetadataBase):
    old_stock = models.ForeignKey(
        Stock, related_name="outgoing_transfers", on_delete=models.PROTECT
    )
    new_stock = models.ForeignKey(
        Stock, related_name="incoming_transfers", on_delete=models.PROTECT
    )
    other_item_action = models.OneToOneField(
        StockItemAction,
        on_delete=models.PROTECT,
        related_name="transfer_other_item_metadata",
    )

    def __str__(self):
        return _("transfer %s to stock of id %s") % (
            self.transfer_quantity,
            self.new_stock_id,
        )

    @property
    def added_quantity(self):
        if hasattr(self, "_added_quantity"):
            return self._added_quantity
        return self.item_action.quantity_before - self.item_action.quantity_after

    @added_quantity.setter
    def added_quantity(self, value):
        self._added_quantity = value

    @added_quantity.deleter
    def added_quantity(self):
        self.__dict__.pop("_added_quantity", None)

    @property
    def remove_quantity(self):
        if hasattr(self, "_added_quantity"):
            return self._added_quantity
        return self.item_action.quantity_before - self.item_action.quantity_after
