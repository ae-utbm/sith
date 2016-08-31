from django.db import models, DataError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError

from datetime import timedelta
import random
import string

from club.models import Club
from accounting.models import CurrencyField
from core.models import Group, User
from subscription.models import Subscriber
from subscription.views import get_subscriber

class Customer(models.Model):
    """
    This class extends a user to make a customer. It adds some basic customers informations, such as the accound ID, and
    is used by other accounting classes as reference to the customer, rather than using User
    """
    user = models.OneToOneField(User, primary_key=True)
    account_id = models.CharField(_('account id'), max_length=10, unique=True)
    amount = CurrencyField(_('amount'))

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        ordering = ['account_id',]

    def __str__(self):
        return "%s - %s" % (self.user.username, self.account_id)

    def generate_account_id(number):
        number = str(number)
        letter = random.choice(string.ascii_lowercase)
        while Customer.objects.filter(account_id=number+letter).exists():
            letter = random.choice(string.ascii_lowercase)
        return number+letter

    def save(self, *args, **kwargs):
        if self.amount < 0:
            raise ValidationError(_("Not enough money"))
        super(Customer, self).save(*args, **kwargs)

class ProductType(models.Model):
    """
    This describes a product type
    Useful only for categorizing, changes are made at the product level for now
    """
    name = models.CharField(_('name'), max_length=30)
    description = models.TextField(_('description'), null=True, blank=True)
    icon = models.ImageField(upload_to='products', null=True, blank=True)

    class Meta:
        verbose_name = _('product type')

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('counter:producttype_list')

class Product(models.Model):
    """
    This describes a product, with all its related informations
    """
    name = models.CharField(_('name'), max_length=64)
    description = models.TextField(_('description'), blank=True)
    product_type = models.ForeignKey(ProductType, related_name='products', verbose_name=_("product type"), null=True, blank=True,
            on_delete=models.SET_NULL)
    code = models.CharField(_('code'), max_length=16, blank=True)
    purchase_price = CurrencyField(_('purchase price'))
    selling_price = CurrencyField(_('selling price'))
    special_selling_price = CurrencyField(_('special selling price'))
    icon = models.ImageField(upload_to='products', null=True, blank=True, verbose_name=_("icon"))
    club = models.ForeignKey(Club, related_name="products", verbose_name=_("club"))
    limit_age = models.IntegerField(_('limit age'), default=0)
    tray = models.BooleanField(_('tray price'), default=False)
    parent_product = models.ForeignKey('self', related_name='children_products', verbose_name=_("parent product"), null=True,
            blank=True, on_delete=models.SET_NULL)
    buying_groups = models.ManyToManyField(Group, related_name='products', verbose_name=_("buying groups"), blank=True)

    class Meta:
        verbose_name = _('product')

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('counter:product_list')

class Counter(models.Model):
    name = models.CharField(_('name'), max_length=30)
    club = models.ForeignKey(Club, related_name="counters", verbose_name=_("club"))
    products = models.ManyToManyField(Product, related_name="counters", verbose_name=_("products"), blank=True)
    type = models.CharField(_('counter type'),
            max_length=255,
            choices=[('BAR',_('Bar')), ('OFFICE',_('Office')), ('EBOUTIC',_('Eboutic'))])
    sellers = models.ManyToManyField(Subscriber, verbose_name=_('sellers'), related_name='counters', blank=True)
    edit_groups = models.ManyToManyField(Group, related_name="editable_counters", blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_counters", blank=True)

    class Meta:
        verbose_name = _('counter')

    def __getattribute__(self, name):
        if name == "edit_groups":
            return Group.objects.filter(name=self.club.unix_name+settings.SITH_BOARD_SUFFIX).all()
        return object.__getattribute__(self, name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.type == "EBOUTIC":
            return reverse('eboutic:main')
        return reverse('counter:details', kwargs={'counter_id': self.id})

    def is_owned_by(self, user):
        mem = self.club.get_membership_for(user)
        if mem and mem.role >= 7:
            return True
        return user.is_in_group(settings.SITH_GROUPS['counter-admin']['name'])

    def can_be_viewed_by(self, user):
        if self.type == "BAR" or self.type == "EBOUTIC":
            return True
        sub = get_subscriber(request.user)
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP) or sub in self.sellers

    def add_barman(self, user):
        """
        Logs a barman in to the given counter
        A user is stored as a tuple with its login time
        """
        Permanency(user=user, counter=self, start=timezone.now(), end=None).save()

    def del_barman(self, user):
        """
        Logs a barman out and store its permanency
        """
        perm = Permanency.objects.filter(counter=self, user=user, end=None).all()
        for p in perm:
            p.end = p.activity
            p.save()

    def get_barmen_list(self):
        """
        Returns the barman list as list of User

        Also handle the timeout of the barmen
        """
        pl = Permanency.objects.filter(counter=self, end=None).all()
        bl = []
        for p in pl:
            if timezone.now() - p.activity < timedelta(minutes=settings.SITH_BARMAN_TIMEOUT):
                p.save() # Update activity
                bl.append(p.user)
            else:
                p.end = p.activity
                p.save()
        return bl

    def get_random_barman(self):
        bl = self.get_barmen_list()
        return bl[random.randrange(0, len(bl))]

    def is_open(self):
        response = False
        if len(self.get_barmen_list()) > 0:
            response = True
        return response

    def barman_list(self):
        return [b.id for b in self.get_barmen_list()]

class Refilling(models.Model):
    """
    Handle the refilling
    """
    counter = models.ForeignKey(Counter, related_name="refillings", blank=False)
    amount = CurrencyField(_('amount'))
    operator = models.ForeignKey(User, related_name="refillings_as_operator", blank=False)
    customer = models.ForeignKey(Customer, related_name="refillings", blank=False)
    date = models.DateTimeField(_('date'))
    payment_method = models.CharField(_('payment method'), max_length=255,
            choices=settings.SITH_COUNTER_PAYMENT_METHOD, default='CASH')
    bank = models.CharField(_('bank'), max_length=255,
            choices=settings.SITH_COUNTER_BANK, default='OTHER')
    is_validated = models.BooleanField(_('is validated'), default=False)

    class Meta:
        verbose_name = _("refilling")

    def __str__(self):
        return "Refilling: %.2f for %s" % (self.amount, self.customer.user.get_display_name())

    def is_owned_by(self, user):
        return user.is_owner(self.counter) and self.payment_method != "CARD"

    def delete(self, *args, **kwargs):
        self.customer.amount -= self.amount
        self.customer.save()
        super(Refilling, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()
        self.full_clean()
        if not self.is_validated:
            self.customer.amount += self.amount
            self.customer.save()
            self.is_validated = True
        super(Refilling, self).save(*args, **kwargs)

class Selling(models.Model):
    """
    Handle the sellings
    """
    label = models.CharField(_("label"), max_length=64)
    product = models.ForeignKey(Product, related_name="sellings", null=True, blank=True, on_delete=models.SET_NULL)
    counter = models.ForeignKey(Counter, related_name="sellings", null=True, blank=False, on_delete=models.SET_NULL)
    club = models.ForeignKey(Club, related_name="sellings", null=True, blank=False, on_delete=models.SET_NULL)
    unit_price = CurrencyField(_('unit price'))
    quantity = models.IntegerField(_('quantity'))
    seller = models.ForeignKey(User, related_name="sellings_as_operator", null=True, blank=False, on_delete=models.SET_NULL)
    customer = models.ForeignKey(Customer, related_name="buyings", null=True, blank=False, on_delete=models.SET_NULL)
    date = models.DateTimeField(_('date'))
    payment_method = models.CharField(_('payment method'), max_length=255,
            choices=[('SITH_ACCOUNT', _('Sith account')), ('CARD', _('Credit card'))], default='SITH_ACCOUNT')
    is_validated = models.BooleanField(_('is validated'), default=False)

    class Meta:
        verbose_name = _("selling")

    def __str__(self):
        return "Selling: %d x %s (%f) for %s" % (self.quantity, self.label,
                self.quantity*self.unit_price, self.customer.user.get_display_name())

    def is_owned_by(self, user):
        return user.is_owner(self.counter) and self.payment_method != "CARD"

    def delete(self, *args, **kwargs):
        self.customer.amount += self.quantity * self.unit_price
        self.customer.save()
        super(Selling, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()
        self.full_clean()
        if not self.is_validated:
            self.customer.amount -= self.quantity * self.unit_price
            self.customer.save()
            self.is_validated = True
        super(Selling, self).save(*args, **kwargs)

class Permanency(models.Model):
    """
    This class aims at storing a traceability of who was barman where and when
    """
    user = models.ForeignKey(User, related_name="permanencies", verbose_name=_("user"))
    counter = models.ForeignKey(Counter, related_name="permanencies", verbose_name=_("counter"))
    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'), null=True)
    activity = models.DateTimeField(_('last activity date'), auto_now=True)

    class Meta:
        verbose_name = _("permanency")

    def __str__(self):
        return "%s in %s from %s" % (self.user, self.counter,
                self.start.strftime("%Y-%m-%d %H:%M:%S"))

class CashRegisterSummary(models.Model):
    user = models.ForeignKey(User, related_name="cash_summaries", verbose_name=_("user"))
    counter = models.ForeignKey(Counter, related_name="cash_summaries", verbose_name=_("counter"))
    date = models.DateTimeField(_('date'))
    comment = models.TextField(_('comment'), null=True, blank=True)
    emptied = models.BooleanField(_('emptied'), default=False)

    class Meta:
        verbose_name = _("cash register summary")

    def __str__(self):
        return "At %s by %s - Total: %s €" % (self.counter, self.user, self.get_total())

    def get_total(self):
        t = 0
        for it in self.items.all():
            t += it.quantity * it.value
        return t

    def save(self, *args, **kwargs):
        if not self.id:
            self.date = timezone.now()
        return super(CashRegisterSummary, self).save(*args, **kwargs)

class CashRegisterSummaryItem(models.Model):
    cash_summary = models.ForeignKey(CashRegisterSummary, related_name="items", verbose_name=_("cash summary"))
    value = CurrencyField(_("value"))
    quantity = models.IntegerField(_('quantity'), default=0)
    check = models.BooleanField(_('check'), default=False)

    class Meta:
        verbose_name = _("cash register summary item")

