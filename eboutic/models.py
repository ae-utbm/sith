from django.db import models, DataError
from django.utils.translation import ugettext_lazy as _

from accounting.models import CurrencyField
from counter.models import Counter, Product
from core.models import User

class Basket(models.Model):
    """
    Basket is built when the user validate its session basket and asks for payment
    """
    user = models.ForeignKey(User, related_name='baskets', verbose_name=_('user'), blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)

    def get_total(self):
        total = 0
        for i in self.items.all():
            total += i.quantity * i.product_unit_price
        return total

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
        if self.payment_method == "SITH_ACCOUNT":
            self.user.customer.amount -= self.get_total()
            self.user.customer.save()
        self.validated = True
        self.save()



class AbstractBaseItem(models.Model):
    product_name = models.CharField(_('product name'), max_length=255)
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
