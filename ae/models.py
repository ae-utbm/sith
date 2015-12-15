from datetime import date, timedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from core.models import User

def validate_type(value):
    if value not in settings.AE_SUBSCRIPTIONS.keys():
        raise ValidationError(_('Bad subscription type'))

def validate_payment(value):
    if value not in settings.AE_PAYMENT_METHOD:
        raise ValidationError(_('Bad payment method'))

class Member(models.Model):
    user = models.OneToOneField(User, primary_key=True)

    def is_subscribed(self):
        return self.subscriptions.last().is_valid_now()

class Subscription(models.Model):
    member = models.ForeignKey(Member, related_name='subscriptions')
    subscription_type = models.CharField(_('subscription type'),
                                         max_length=255,
                                         choices=((k.lower().replace(' ', '-'), k) for k in sorted(settings.AE_SUBSCRIPTIONS.keys())))
    subscription_start = models.DateField(_('subscription start'))
    subscription_end = models.DateField(_('subscription end'))
    payment_method = models.CharField(_('payment method'), max_length=255, choices=settings.AE_PAYMENT_METHOD)

    class Meta:
        ordering = ['subscription_start',]

    @staticmethod
    def compute_start(d=date.today()):
        """
        This function computes the start date of the subscription with respect to the given date (default is today),
        and the start date given in settings.AE_START_DATE.
        It takes the nearest past start date.
        Exemples: with AE_START_DATE = (8, 15)
            Today      -> Start date
            2015-03-17 -> 2015-02-15
            2015-01-11 -> 2014-08-15
        """
        today = d
        year = today.year
        start = date(year, settings.AE_START_DATE[0], settings.AE_START_DATE[1])
        start2 = start.replace(month=(start.month+6)%12)
        if start > start2:
            start, start2 = start2, start
        if today < start:
            return start2.replace(year=year-1)
        elif today < start2:
            return start
        else:
            return start2

    @staticmethod
    def compute_end(duration, start=None):
        """
        This function compute the end date of the subscription given a start date and a duration in number of semestre
        Exemple:
            Start - Duration -> End date
            2015-09-18 - 1 -> 2016-03-18
            2015-09-18 - 2 -> 2016-09-18
            2015-09-18 - 3 -> 2017-03-18
            2015-09-18 - 4 -> 2017-09-18
        """
        if start is None:
            start = Subscription.compute_start()
        # This can certainly be simplified, but it works like this
        return start.replace(month=(start.month+6*duration)%12,
                             year=start.year+int(duration/2)+(1 if start.month > 6 and duration%2 == 1 else 0))

    def is_valid_now(self):
        return self.subscription_start <= date.today() and date.today() <= self.subscription_end

def guy_test(date):
    print(str(date)+" -> "+str(Subscription.compute_start(date)))
def bibou_test(duration, date=None):
    print(str(date)+" - "+str(duration)+" -> "+str(Subscription.compute_end(duration, date)))
def guy():
    guy_test(date(2015, 7, 11))
    guy_test(date(2015, 8, 11))
    guy_test(date(2015, 2, 17))
    guy_test(date(2015, 3, 17))
    guy_test(date(2015, 1, 11))
    guy_test(date(2015, 2, 11))
    guy_test(date(2015, 8, 17))
    guy_test(date(2015, 9, 17))
    print('='*80)
    bibou_test(1, date(2015, 2, 18))
    bibou_test(2, date(2015, 2, 18))
    bibou_test(3, date(2015, 2, 18))
    bibou_test(4, date(2015, 2, 18))
    bibou_test(1, date(2015, 9, 18))
    bibou_test(2, date(2015, 9, 18))
    bibou_test(3, date(2015, 9, 18))
    bibou_test(4, date(2015, 9, 18))
    bibou_test(1)
    bibou_test(2)
    bibou_test(3)
    bibou_test(4)

if __name__ == "__main__":
    guy()
