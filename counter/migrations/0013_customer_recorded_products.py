# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.db import migrations, models
from django.conf import settings

from core.models import User
from counter.models import Customer, Product, Selling, Counter


def balance_ecocups(apps, schema_editor):
    for customer in Customer.objects.all():
        customer.recorded_products = 0
        for selling in customer.buyings.filter(
            product__id__in=[settings.SITH_ECOCUP_CONS, settings.SITH_ECOCUP_DECO]
        ).all():
            if selling.product.is_record_product:
                customer.recorded_products += selling.quantity
            elif selling.product.is_unrecord_product:
                customer.recorded_products -= selling.quantity
        if customer.recorded_products < -settings.SITH_ECOCUP_LIMIT:
            qt = -(customer.recorded_products + settings.SITH_ECOCUP_LIMIT)
            cons = Product.objects.get(id=settings.SITH_ECOCUP_CONS)
            Selling(
                label=_("Ecocup regularization"),
                product=cons,
                unit_price=cons.selling_price,
                club=cons.club,
                counter=Counter.objects.filter(name="Foyer").first(),
                quantity=qt,
                seller=User.objects.get(id=0),
                customer=customer,
            ).save(allow_negative=True)
            customer.recorded_products += qt
        customer.save()


class Migration(migrations.Migration):

    dependencies = [("counter", "0012_auto_20170515_2202")]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="recorded_products",
            field=models.IntegerField(verbose_name="recorded items", default=0),
        ),
        migrations.RunPython(balance_ecocups),
    ]
