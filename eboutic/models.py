from django.db import models, DataError
from django.utils.translation import ugettext_lazy as _

from accounting.models import CurrencyField
from counter.models import Counter, Product, Customer
from core.models import User

class Basket(models.Model):
    """
    Basket is built when the user connects to an eboutic page
    """
    user = models.ForeignKey(User, related_name='baskets', verbose_name=_('user'), blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)

    def add_product(self, p, q = 1):
        item = self.items.filter(product_id=p.id).first()
        if item is None:
            BasketItem(basket=self, product_id=p.id, product_name=p.name, type=p.product_type.name,
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
        return "Basket (%d items)" % self.items.all().count()

class Invoice(models.Model):
    """
    Invoices are generated once the payment has been validated
    """
    user = models.ForeignKey(User, related_name='invoices', verbose_name=_('user'), blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)
    payment_method = models.CharField(choices=[('CREDIT_CARD', _('Credit card')), ('SITH_ACCOUNT', _('Sith account'))],
            max_length=20, verbose_name=_('payment method'))
    validated = models.BooleanField(_("validated"), default=False)

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
            number = Customer.objects.last().account_id[:-1]
            Customer(user=self.user, account_id=Customer.generate_account_id(number), amount=0).save()
        if self.payment_method == "SITH_ACCOUNT":
            self.user.customer.amount -= self.get_total()
            self.user.customer.save()
        else:
            for i in self.items.filter(type="REFILLING").all():
                self.user.customer.amount += i.product_unit_price * i.quantity
            self.user.customer.save()

        self.validated = True
        self.save()

class AbstractBaseItem(models.Model):
    product_id = models.IntegerField(_('product id'))
    product_name = models.CharField(_('product name'), max_length=255)
    type = models.CharField(_('product type'), max_length=255)
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
