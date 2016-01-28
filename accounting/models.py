from django.db import models
from django.utils.translation import ugettext_lazy as _

from decimal import Decimal
from core.models import User

class CurrencyField(models.DecimalField):
    """
    This is a custom database field used for currency
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 12
        kwargs['decimal_places'] = 2
        super(CurrencyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        try:
           return super(CurrencyField, self).to_python(value).quantize(Decimal("0.01"))
        except AttributeError:
           return None

class Customer(models.Model):
    """
    This class extends a user to make a customer. It adds some basic customers informations, such as the accound ID, and
    is used by other accounting classes as reference to the customer, rather than using User
    """
    user = models.OneToOneField(User, primary_key=True)
    account_id = models.CharField(_('account id'), max_length=10, unique=True)

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self):
        return self.user.username

class ProductType(models.Model):
    """
    This describes a product type
    Useful only for categorizing, changes are made at the product level
    """
    name = models.CharField(_('name'), max_length=30)
    description = models.TextField(_('description'), null=True, blank=True)
    icon = models.ImageField(upload_to='products', null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    This describes a product, with all its related informations
    """
    name = models.CharField(_('name'), max_length=30)
    description = models.TextField(_('description'), blank=True)
    product_type = models.ForeignKey(ProductType, related_name='products', null=True, blank=True)
    code = models.CharField(_('code'), max_length=10)
    purchase_price = CurrencyField(_('purchase price'))
    selling_price = CurrencyField(_('selling price'))
    special_selling_price = CurrencyField(_('special selling price'))
    icon = models.ImageField(upload_to='products', null=True, blank=True)

    def __str__(self):
        return self.name

class GeneralJournal(models.Model):
    """
    Class storing all the invoices for a period of time
    """
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True, default=None)
    name = models.CharField(_('name'), max_length=30)
    closed = models.BooleanField(_('is closed'), default=False)
    # When clubs are done: ForeignKey(Proprietary)

    def __str__(self):
        return self.name


class GenericInvoice(models.Model):
    """
    This class is a generic invoice, made to be extended with some special cases (eg: for the internal accounting, payment
    system, etc...)
    """
    journal = models.ForeignKey(GeneralJournal, related_name="invoices", null=False)
    name = models.CharField(_('name'), max_length=100)

    def __str__(self):
        return self.journal.name+' - '+self.name


# TODO: CountingInvoice in Counting app extending GenericInvoice
#       - ManyToMany Product
