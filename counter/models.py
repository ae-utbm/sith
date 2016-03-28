from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from club.models import Club
from accounting.models import Product
from core.models import Group

class Counter(models.Model):
    name = models.CharField(_('name'), max_length=30)
    club = models.ForeignKey(Club, related_name="counters")
    products = models.ManyToManyField(Product, related_name="counters", blank=True)
    edit_groups = models.ManyToManyField(Group, related_name="editable_counters", blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_counters", blank=True)

    def __getattribute__(self, name):
        if name == "owner_group":
            return Group(name=self.club.unix_name+"-board")
        return object.__getattribute__(self, name)

    def __str__(self):
        return self.name
