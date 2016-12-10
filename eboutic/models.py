from django.db import models, DataError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from accounting.models import CurrencyField
from counter.models import Counter, Product, Customer, Selling, Refilling
from core.models import User
from subscription.models import Subscription

class Basket(models.Model):
    """
    Basket is built when the user connects to an eboutic page
    """
    user = models.ForeignKey(User, related_name='baskets', verbose_name=_('user'), blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)

    def add_product(self, p, q = 1):
        item = self.items.filter(product_id=p.id).first()
        if item is None:
            BasketItem(basket=self, product_id=p.id, product_name=p.name, type_id=p.product_type.id,
                    quantity=q, product_unit_price=p.selling_price).save()
        else:
            item.quantity += q
            item.save()

    def del_product(self, p, q = 1):
        item = self.items.filter(product_id=p.id).first()
        if item is not None:
            item.quantity -= q
            item.save()
        if item.quantity <= 0:
            item.delete()

    def get_total(self):
        total = 0
        for i in self.items.all():
            total += i.quantity * i.product_unit_price
        return total

    def __str__(self):
        return "%s's basket (%d items)" % (self.user, self.items.all().count())

class Invoice(models.Model):
    """
    Invoices are generated once the payment has been validated
    """
    user = models.ForeignKey(User, related_name='invoices', verbose_name=_('user'), blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)
    validated = models.BooleanField(_("validated"), default=False)

    def __str__(self):
        return "%s - %s - %s" % (self.user, self.get_total(), self.date)

    def get_total(self):
        total = 0
        for i in self.items.all():
            total += i.quantity * i.product_unit_price
        return total

    def validate(self, *args, **kwargs):
        if self.validated:
            raise DataError(_("Invoice already validated"))
        from counter.models import Customer
        if not Customer.objects.filter(user=self.user).exists():
            number = Customer.objects.count() + 1
            Customer(user=self.user, account_id=Customer.generate_account_id(number), amount=0).save()
        eboutic = Counter.objects.filter(type="EBOUTIC").first()
        for i in self.items.all():
            if i.type_id == settings.SITH_COUNTER_PRODUCTTYPE_REFILLING:
                new = Refilling(
                        counter=eboutic,
                        customer=self.user.customer,
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
                        customer=self.user.customer,
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
    product_id = models.IntegerField(_('product id'))
    product_name = models.CharField(_('product name'), max_length=255)
    type_id = models.IntegerField(_('product type id'))
    product_unit_price = CurrencyField(_('unit price'))
    quantity = models.IntegerField(_('quantity'))

    class Meta:
        abstract = True

    def __str__(self):
        return "Item: %s (%s) x%d" % (self.product_name, self.product_unit_price, self.quantity)

class BasketItem(AbstractBaseItem):
    basket = models.ForeignKey(Basket, related_name='items', verbose_name=_('basket'))

class InvoiceItem(AbstractBaseItem):
    invoice = models.ForeignKey(Invoice, related_name='items', verbose_name=_('invoice'))
