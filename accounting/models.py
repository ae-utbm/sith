from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core import validators
from django.db.models import Count
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.template import defaultfilters

from phonenumber_field.modelfields import PhoneNumberField

from decimal import Decimal
from core.models import User, SithFile
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

# Accounting classes

class Company(models.Model):
    name = models.CharField(_('name'), max_length=60)
    street = models.CharField(_('street'), max_length=60, blank=True)
    city = models.CharField(_('city'), max_length=60, blank=True)
    postcode = models.CharField(_('postcode'), max_length=10, blank=True)
    country = models.CharField(_('country'), max_length=32, blank=True)
    phone = PhoneNumberField(_('phone'), blank=True)
    email = models.EmailField(_('email'), blank=True)
    website = models.CharField(_('website'), max_length=64, blank=True)

    class Meta:
        verbose_name = _("company")

    def get_absolute_url(self):
        return reverse('accounting:co_edit', kwargs={'co_id': self.id})

    def get_display_name(self):
        return self.name

    def __str__(self):
        return self.name

class BankAccount(models.Model):
    name = models.CharField(_('name'), max_length=30)
    iban = models.CharField(_('iban'), max_length=255, blank=True)
    number = models.CharField(_('account number'), max_length=255, blank=True)
    club = models.ForeignKey(Club, related_name="bank_accounts", verbose_name=_("club"))

    class Meta:
        verbose_name = _("Bank account")
        ordering = ['club', 'name']

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
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
    club = models.ForeignKey(Club, related_name="club_account", verbose_name=_("club"))
    bank_account = models.ForeignKey(BankAccount, related_name="club_accounts", verbose_name=_("bank account"))

    class Meta:
        verbose_name = _("Club account")
        ordering = ['bank_account', 'name']

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
            return True
        return False

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        m = self.club.get_membership_for(user)
        if m and m.role == 7:
            return True
        return False

    def can_be_viewed_by(self, user):
        """
        Method to see if that object can be viewed by the given user
        """
        m = self.club.get_membership_for(user)
        if m and m.role >= 7:
            return True
        return False

    def has_open_journal(self):
        for j in self.journals.all():
            if not j.closed:
                return True
        return False

    def get_open_journal(self):
        return self.journals.filter(closed=False).first()

    def get_absolute_url(self):
        return reverse('accounting:club_details', kwargs={'c_account_id': self.id})

    def __str__(self):
        return self.name

    def get_display_name(self):
        return _("%(club_account)s on %(bank_account)s") % {"club_account": self.name, "bank_account": self.bank_account}


class GeneralJournal(models.Model):
    """
    Class storing all the operations for a period of time
    """
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True, default=None)
    name = models.CharField(_('name'), max_length=40)
    closed = models.BooleanField(_('is closed'), default=False)
    club_account = models.ForeignKey(ClubAccount, related_name="journals", null=False, verbose_name=_("club account"))
    amount = CurrencyField(_('amount'), default=0)
    effective_amount = CurrencyField(_('effective_amount'), default=0)

    class Meta:
        verbose_name = _("General journal")
        ordering = ['-start_date']

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
            return True
        if self.club_account.can_be_edited_by(user):
            return True
        return False

    def can_be_viewed_by(self, user):
        return self.club_account.can_be_edited_by(user)

    def get_absolute_url(self):
        return reverse('accounting:journal_details', kwargs={'j_id': self.id})

    def __str__(self):
        return self.name

    def update_amounts(self):
        self.amount = 0
        self.effective_amount = 0
        for o in self.operations.all():
            if o.accounting_type.movement_type == "CREDIT":
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
    number = models.IntegerField(_('number'))
    journal = models.ForeignKey(GeneralJournal, related_name="operations", null=False, verbose_name=_("journal"))
    amount = CurrencyField(_('amount'))
    date = models.DateField(_('date'))
    remark = models.CharField(_('comment'), max_length=128)
    mode = models.CharField(_('payment method'), max_length=255, choices=settings.SITH_ACCOUNTING_PAYMENT_METHOD)
    cheque_number = models.CharField(_('cheque number'), max_length=32, default="", null=True, blank=True)
    invoice = models.ForeignKey(SithFile, related_name='operations', verbose_name=_("invoice"), null=True, blank=True)
    done = models.BooleanField(_('is done'), default=False)
    simpleaccounting_type = models.ForeignKey('SimplifiedAccountingType', related_name="operations",
            verbose_name=_("simple type"), null=True, blank=True)
    accounting_type = models.ForeignKey('AccountingType', related_name="operations",
            verbose_name=_("accounting type"), null=True, blank=True)
    label = models.ForeignKey('Label', related_name="operations",
            verbose_name=_("label"), null=True, blank=True, on_delete=models.SET_NULL)
    target_type = models.CharField(_('target type'), max_length=10,
            choices=[('USER', _('User')), ('CLUB', _('Club')), ('ACCOUNT', _('Account')), ('COMPANY', _('Company')), ('OTHER', _('Other'))])
    target_id = models.IntegerField(_('target id'), null=True, blank=True)
    target_label = models.CharField(_('target label'), max_length=32, default="", blank=True)
    linked_operation = models.OneToOneField('self', related_name='operation_linked_to', verbose_name=_("linked operation"),
            null=True, blank=True, default=None)

    class Meta:
        unique_together = ('number', 'journal')
        ordering = ['-number']

    def __getattribute__(self, attr):
        if attr == "target":
            return self.get_target()
        else:
            return object.__getattribute__(self, attr)

    def clean(self):
        super(Operation, self).clean()
        if self.date < self.journal.start_date:
            raise ValidationError(_("""The date can not be before the start date of the journal, which is
%(start_date)s.""") % {'start_date': defaultfilters.date(self.journal.start_date, settings.DATE_FORMAT)})
        if self.target_type != "OTHER" and self.get_target() is None:
            raise ValidationError(_("Target does not exists"))
        if self.target_type == "OTHER" and self.target_label == "":
            raise ValidationError(_("Please add a target label if you set no existing target"))
        if not self.accounting_type and not self.simpleaccounting_type:
            raise ValidationError(_("You need to provide ether a simplified accounting type or a standard accounting type"))
        if self.simpleaccounting_type:
            self.accounting_type = self.simpleaccounting_type.accounting_type

    @property
    def target(self):
        return self.get_target()

    def get_target(self):
        tar = None
        if self.target_type == "USER":
            tar = User.objects.filter(id=self.target_id).first()
        elif self.target_type == "CLUB":
            tar = Club.objects.filter(id=self.target_id).first()
        elif self.target_type == "ACCOUNT":
            tar = ClubAccount.objects.filter(id=self.target_id).first()
        elif self.target_type == "COMPANY":
            tar = Company.objects.filter(id=self.target_id).first()
        return tar

    def save(self):
        if self.number is None:
            self.number = self.journal.operations.count() + 1
        super(Operation, self).save()
        self.journal.update_amounts()

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
            return True
        if self.journal.closed:
            return False
        m = self.journal.club_account.club.get_membership_for(user)
        if m is not None and m.role >= 7:
            return True
        return False

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if self.is_owned_by(user):
            return True
        return False

    def get_absolute_url(self):
        return reverse('accounting:journal_details', kwargs={'j_id': self.journal.id})

    def __str__(self):
        return "%d € | %s | %s | %s" % (
                self.amount, self.date, self.accounting_type, self.done,
                )

class AccountingType(models.Model):
    """
    Class describing the accounting types.

    Thoses are numbers used in accounting to classify operations
    """
    code = models.CharField(_('code'), max_length=16,
            validators=[
                validators.RegexValidator(r'^[0-9]*$', _('An accounting type code contains only numbers')),
                ],
            )
    label = models.CharField(_('label'), max_length=128)
    movement_type = models.CharField(_('movement type'), choices=[('CREDIT', _('Credit')), ('DEBIT', _('Debit')),
            ('NEUTRAL', _('Neutral'))], max_length=12)

    class Meta:
        verbose_name = _("accounting type")
        ordering = ['movement_type', 'code']

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
            return True
        return False

    def get_absolute_url(self):
        return reverse('accounting:type_list')

    def __str__(self):
        return self.code+" - "+self.get_movement_type_display()+" - "+self.label

class SimplifiedAccountingType(models.Model):
    """
    Class describing the simplified accounting types.
    """
    label = models.CharField(_('label'), max_length=128)
    accounting_type = models.ForeignKey(AccountingType, related_name="simplified_types",
            verbose_name=_("simplified accounting types"))

    class Meta:
        verbose_name = _("simplified type")
        ordering = ['accounting_type__movement_type', 'accounting_type__code']

    @property
    def movement_type(self):
        return self.accounting_type.movement_type

    def get_movement_type_display(self):
        return self.accounting_type.get_movement_type_display()

    def get_absolute_url(self):
        return reverse('accounting:simple_type_list')

    def __str__(self):
        return self.get_movement_type_display()+" - "+self.accounting_type.code+" - "+self.label

class Label(models.Model):
    """Label allow a club to sort its operations"""
    name = models.CharField(_('label'), max_length=64)
    club_account = models.ForeignKey(ClubAccount, related_name="labels", verbose_name=_("club account"))

    class Meta:
        unique_together = ('name', 'club_account')

    def __str__(self):
        return "%s (%s)" % (self.name, self.club_account.name)

    def get_absolute_url(self):
        return reverse('accounting:label_list', kwargs={'clubaccount_id': self.club_account.id})

    def is_owned_by(self, user):
        return self.club_account.is_owned_by(user)

    def can_be_edited_by(self, user):
        return self.club_account.can_be_edited_by(user)

    def can_be_viewed_by(self, user):
        return self.club_account.can_be_viewed_by(user)

