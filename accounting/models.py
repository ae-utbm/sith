from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from decimal import Decimal
from core.models import User
from club.models import Club

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
    Useful only for categorizing, changes are made at the product level for now
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

class BankAccount(models.Model):
    name = models.CharField(_('name'), max_length=30)
    rib = models.CharField(_('rib'), max_length=255, blank=True)
    number = models.CharField(_('account number'), max_length=255, blank=True)

    def get_absolute_url(self):
        return reverse('accounting:bank_details', kwargs={'b_account_id': self.id})

    def __str__(self):
        return self.name

class ClubAccount(models.Model):
    name = models.CharField(_('name'), max_length=30)
    club = models.OneToOneField(Club, related_name="club_accounts")
    bank_account = models.ForeignKey(BankAccount, related_name="club_accounts")

    def get_absolute_url(self):
        return reverse('accounting:club_details', kwargs={'c_account_id': self.id})

    def __str__(self):
        return self.name

class GeneralJournal(models.Model):
    """
    Class storing all the operations for a period of time
    """
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True, default=None)
    name = models.CharField(_('name'), max_length=30)
    closed = models.BooleanField(_('is closed'), default=False)
    club_account = models.ForeignKey(ClubAccount, related_name="journals", null=False)

    def __str__(self):
        return self.name

class AccountingType(models.Model):
    """
    Class describing the accounting types.

    Thoses are numbers used in accounting to classify operations
    """
    code = models.CharField(_('code'), max_length=16) # TODO: add number validator
    label = models.CharField(_('label'), max_length=60)
    movement_type = models.CharField(_('movement type'), choices=[('credit', 'Credit'), ('debit', 'Debit'), ('neutral', 'Neutral')], max_length=12)

class Operation(models.Model):
    """
    An operation is a line in the journal, a debit or a credit
    """
    journal = models.ForeignKey(GeneralJournal, related_name="invoices", null=False)
    date = models.DateField(_('date'))
    remark = models.TextField(_('remark'), max_length=255)
    mode = models.CharField(_('payment method'), max_length=255, choices=settings.SITH_ACCOUNTING_PAYMENT_METHOD)
    cheque_number = models.IntegerField(_('cheque number'))
    invoice = models.FileField(upload_to='invoices', null=True, blank=True)
    done = models.BooleanField(_('is done'), default=False)
    type = models.ForeignKey(AccountingType, related_name="operations")

    def __str__(self):
        return self.journal.name+' - '+self.name

