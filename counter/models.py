from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

from club.models import Club
from accounting.models import Product
from core.models import Group

class Counter(models.Model):
    name = models.CharField(_('name'), max_length=30)
    club = models.ForeignKey(Club, related_name="counters")
    products = models.ManyToManyField(Product, related_name="counters", blank=True)
    type = models.CharField(_('subscription type'),
            max_length=255,
            choices=[('BAR',_('Bar')), ('OFFICE',_('Office'))])
    edit_groups = models.ManyToManyField(Group, related_name="editable_counters", blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_counters", blank=True)

    def __getattribute__(self, name):
        if name == "owner_group":
            return Group(name=self.club.unix_name+settings.SITH_BOARD_SUFFIX)
        return object.__getattribute__(self, name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('counter:details', kwargs={'counter_id': self.id})

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP)
