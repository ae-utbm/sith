from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse

from datetime import timedelta

from club.models import Club
from accounting.models import CurrencyField
from core.models import Group, User
from subscription.models import Subscriber

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

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

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
    club = models.ForeignKey(Club, related_name="products")

    def is_owned_by(self, user): # TODO do this for all models
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name']):
            return True
        return False

    def __str__(self):
        return self.name

class Counter(models.Model):
    name = models.CharField(_('name'), max_length=30)
    club = models.ForeignKey(Club, related_name="counters")
    products = models.ManyToManyField(Product, related_name="counters", blank=True)
    type = models.CharField(_('subscription type'),
            max_length=255,
            choices=[('BAR',_('Bar')), ('OFFICE',_('Office'))])
    edit_groups = models.ManyToManyField(Group, related_name="editable_counters", blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_counters", blank=True)
    barmen_session = {}

    def __getattribute__(self, name):
        if name == "owner_group":
            return Group.objects.filter(name=self.club.unix_name+settings.SITH_BOARD_SUFFIX).first()
        return object.__getattribute__(self, name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('counter:details', kwargs={'counter_id': self.id})

    def can_be_edited_by(self, user):
        return user.is_in_group(settings.SITH_GROUPS['counter-admin']['name'])

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP)

    def get_barmen_list(counter_id):
        bl = []
        counter_id = str(counter_id)
        if counter_id in list(Counter.barmen_session.keys()):
            if (timezone.now() - Counter.barmen_session[counter_id]['time']) < timedelta(minutes=settings.SITH_BARMAN_TIMEOUT):
                for b in Counter.barmen_session[counter_id]['users']:
                    bl.append(Subscriber.objects.filter(id=b).first())
                Counter.barmen_session[counter_id]['time'] = timezone.now()
            else:
                Counter.barmen_session[counter_id]['users'] = set()
        return bl

    def get_random_barman(counter_id): # TODO: improve this function
        bl = Counter.get_barmen_list(counter_id)
        return bl[0]

class Refilling(models.Model):
    """
    Handle the refilling
    """
    counter = models.ForeignKey(Counter, related_name="refillings", blank=False)
    amount = CurrencyField(_('amount'))
    operator = models.ForeignKey(User, related_name="refillings_as_operator", blank=False)
    customer = models.ForeignKey(Customer, related_name="refillings", blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)
    payment_method = models.CharField(_('payment method'), max_length=255,
            choices=settings.SITH_COUNTER_PAYMENT_METHOD, default='cash')
    bank = models.CharField(_('bank'), max_length=255,
            choices=settings.SITH_COUNTER_BANK, default='other')

    def __str__(self):
        return "Refilling: %.2f for %s" % (self.amount, self.customer.user.get_display_name())

    # def get_absolute_url(self):
    #     return reverse('counter:details', kwargs={'counter_id': self.id})

    def save(self, *args, **kwargs):
        self.full_clean()
        self.customer.amount += self.amount
        self.customer.save()
        super(Refilling, self).save(*args, **kwargs)

class Selling(models.Model):
    """
    Handle the sellings
    """
    product = models.ForeignKey(Product, related_name="sellings", blank=False)
    counter = models.ForeignKey(Counter, related_name="sellings", blank=False)
    unit_price = CurrencyField(_('unit price'))
    quantity = models.IntegerField(_('quantity'))
    seller = models.ForeignKey(User, related_name="sellings_as_operator", blank=False)
    customer = models.ForeignKey(Customer, related_name="buyings", blank=False)
    date = models.DateTimeField(_('date'), auto_now=True)

    def __str__(self):
        return "Selling: %d x %s (%f) for %s" % (self.quantity, self.product.name,
                self.quantity*self.unit_price, self.customer.user.get_display_name())

    def save(self, *args, **kwargs):
        self.full_clean()
        self.customer.amount -= self.quantity * self.unit_price
        self.customer.save()
        super(Selling, self).save(*args, **kwargs)

    # def get_absolute_url(self):
    #     return reverse('counter:details', kwargs={'counter_id': self.id})


# TODO:
# une classe Vente
# foreign key vers comptoir, vendeur, client, produit, mais stocker le prix du produit, pour gerer les maj de prix
# une classe Rechargement
# foreign key vers comptoir, vendeur, client, plus montant

