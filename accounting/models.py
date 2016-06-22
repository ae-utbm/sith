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


class BankAccount(models.Model):
    name = models.CharField(_('name'), max_length=30)
    iban = models.CharField(_('iban'), max_length=255, blank=True)
    number = models.CharField(_('account number'), max_length=255, blank=True)
    club = models.ForeignKey(Club, related_name="bank_accounts")

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        m = self.club.get_membership_for(user)
        if m is not None and m.role >= 7:
            return True
        return False

    def get_absolute_url(self):
        return reverse('accounting:bank_details', kwargs={'b_account_id': self.id})

    def __str__(self):
        return self.name

class ClubAccount(models.Model):
    name = models.CharField(_('name'), max_length=30)
    club = models.OneToOneField(Club, related_name="club_account")
    bank_account = models.ForeignKey(BankAccount, related_name="club_accounts")

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        m = self.club.get_membership_for(user)
        if m is not None and m.role >= 7:
            return True
        return False

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
    amount = CurrencyField(_('amount'), default=0)
    effective_amount = CurrencyField(_('effective_amount'), default=0)

    def __init__(self, *args, **kwargs):
        super(GeneralJournal, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.id == None:
            amount = 0
        super(GeneralJournal, self).save(*args, **kwargs)

    def can_be_created_by(user):
        """
        Method to see if an object can be created by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']): # TODO: add the treasurer of the club
            return True
        return False

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if self.club_account.can_be_edited_by(user):
            return True
        return False

    def get_absolute_url(self):
        return reverse('accounting:journal_details', kwargs={'j_id': self.id})

    def __str__(self):
        return self.name

    def update_amounts(self):
        self.amount = 0
        self.effective_amount = 0
        for o in self.operations.all():
            if o.type == "credit":
                if o.done:
                    self.effective_amount += o.amount
                self.amount += o.amount
            else:
                if o.done:
                    self.effective_amount -= o.amount
                self.amount -= o.amount
        self.save()

class Operation(models.Model):
    """
    An operation is a line in the journal, a debit or a credit
    """
    journal = models.ForeignKey(GeneralJournal, related_name="operations", null=False)
    amount = CurrencyField(_('amount'))
    date = models.DateField(_('date'))
    label = models.CharField(_('label'), max_length=50)
    remark = models.TextField(_('remark'), max_length=255)
    mode = models.CharField(_('payment method'), max_length=255, choices=settings.SITH_ACCOUNTING_PAYMENT_METHOD)
    cheque_number = models.IntegerField(_('cheque number'), default=-1)
    invoice = models.FileField(upload_to='invoices', null=True, blank=True)
    done = models.BooleanField(_('is done'), default=False)
    accounting_type = models.ForeignKey('AccountingType', related_name="operations")
    type = models.CharField(_('operation type'), max_length=8, choices=[
        ('debit', _('Debit')),
        ('credit', _('Credit')),
        ])

    def save(self):
        super(Operation, self).save()
        self.journal.update_amounts()

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        m = self.journal.club_account.get_membership_for(user)
        if m is not None and m.role >= 7:
            return True
        return False

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if self.journal.can_be_edited_by(user):
            return True
        return False

    def get_absolute_url(self):
        return reverse('accounting:journal_details', kwargs={'j_id': self.journal.id})

    def __str__(self):
        return "%d | %s | %d € | %s | %s | %s" % (
                self.id, self.type, self.amount, self.date, self.accounting_type, self.done,
                )

class AccountingType(models.Model):
    """
    Class describing the accounting types.

    Thoses are numbers used in accounting to classify operations
    """
    code = models.CharField(_('code'), max_length=16) # TODO: add number validator
    label = models.CharField(_('label'), max_length=60)
    movement_type = models.CharField(_('movement type'), choices=[('credit', 'Credit'), ('debit', 'Debit'), ('neutral', 'Neutral')], max_length=12)

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

    def get_absolute_url(self):
        return reverse('accounting:type_list')

    def __str__(self):
        return self.movement_type+" - "+self.code+" - "+self.label

