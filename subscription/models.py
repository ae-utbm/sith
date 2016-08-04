from datetime import date, timedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from core.models import User

def validate_type(value):
    if value not in settings.SITH_SUBSCRIPTIONS.keys():
        raise ValidationError(_('Bad subscription type'))

def validate_payment(value):
    if value not in settings.SITH_SUBSCRIPTION_PAYMENT_METHOD:
        raise ValidationError(_('Bad payment method'))

class Subscriber(User):
    class Meta:
        proxy = True

    def is_subscribed(self):
        s = self.subscriptions.last()
        return s.is_valid_now() if s is not None else False

class Subscription(models.Model):
    member = models.ForeignKey(Subscriber, related_name='subscriptions')
    subscription_type = models.CharField(_('subscription type'),
                                         max_length=255,
                                         choices=((k, v['name']) for k,v in sorted(settings.SITH_SUBSCRIPTIONS.items())))
    subscription_start = models.DateField(_('subscription start'))
    subscription_end = models.DateField(_('subscription end'))
    payment_method = models.CharField(_('payment method'), max_length=255, choices=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD)
    # TODO add location!

    class Meta:
        ordering = ['subscription_start',]

    def clean(self):
        try:
            for s in Subscription.objects.filter(member=self.member).exclude(pk=self.pk).all():
                if s.is_valid_now():
                    raise ValidationError(_("You can not subscribe many time for the same period"))
        except: # This should not happen, because the form should have handled the data before, but sadly, it still
                # calls the model validation :'(
                # TODO see SubscriptionForm's clean method
            raise ValidationError(_("You are trying to create a subscription without member"))

    def save(self):
        super(Subscription, self).save()
        from counter.models import Customer
        if not Customer.objects.filter(user=self.member).exists():
            Customer(user=self.member, account_id=Customer.generate_account_id(self.id), amount=0).save()

    def get_absolute_url(self):
        return reverse('core:user_profile', kwargs={'user_id': self.member.pk})

    def __str__(self):
        if hasattr(self, "member") and self.member is not None:
            return self.member.username+' - '+str(self.pk)
        else:
            return 'No user - '+str(self.pk)


    @staticmethod
    def compute_start(d=date.today(), duration=1):
        """
        This function computes the start date of the subscription with respect to the given date (default is today),
        and the start date given in settings.SITH_START_DATE.
        It takes the nearest past start date.
        Exemples: with SITH_START_DATE = (8, 15)
            Today      -> Start date
            2015-03-17 -> 2015-02-15
            2015-01-11 -> 2014-08-15
        """
        if duration <= 2: # Sliding subscriptions for 1 or 2 semesters
            return d
        today = d
        year = today.year
        start = date(year, settings.SITH_START_DATE[0], settings.SITH_START_DATE[1])
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
            start = Subscription.compute_start(duration=duration)
        # This can certainly be simplified, but it works like this
        try:
            return start.replace(month=(start.month-1+6*duration)%12+1,
                             year=start.year+int(duration/2)+(1 if start.month > 6 and duration%2 == 1 else 0))
        except ValueError as e:
            return start.replace(day=1, month=(start.month+6*duration)%12+1,
                             year=start.year+int(duration/2)+(1 if start.month > 6 and duration%2 == 1 else 0))


    def can_be_edited_by(self, user):
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP) or user.is_in_group(settings.SITH_GROUPS['root']['name'])

    def is_valid_now(self):
        return self.subscription_start <= date.today() and date.today() <= self.subscription_end

def guy_test(date, duration=4):
    print(str(date)+" - "+str(duration)+" -> "+str(Subscription.compute_start(date, duration)))
def bibou_test(duration, date=date.today()):
    print(str(date)+" - "+str(duration)+" -> "+str(Subscription.compute_end(duration, Subscription.compute_start(date, duration))))
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
    guy_test(date(2015, 7, 11), 1)
    guy_test(date(2015, 8, 11), 2)
    guy_test(date(2015, 2, 17), 3)
    guy_test(date(2015, 3, 17), 4)
    guy_test(date(2015, 1, 11), 1)
    guy_test(date(2015, 2, 11), 2)
    guy_test(date(2015, 8, 17), 3)
    guy_test(date(2015, 9, 17), 4)
    print('='*80)
    bibou_test(1, date(2015, 2, 18))
    bibou_test(2, date(2015, 2, 18))
    bibou_test(3, date(2015, 2, 18))
    bibou_test(4, date(2015, 2, 18))
    bibou_test(1, date(2015, 9, 18))
    bibou_test(2, date(2015, 9, 18))
    bibou_test(3, date(2015, 9, 18))
    bibou_test(4, date(2015, 9, 18))
    print('='*80)
    bibou_test(1, date(2000, 2, 29))
    bibou_test(2, date(2000, 2, 29))
    bibou_test(1, date(2000, 5, 31))
    bibou_test(1, date(2000, 7, 31))
    bibou_test(1)
    bibou_test(2)
    bibou_test(3)
    bibou_test(4)

if __name__ == "__main__":
    guy()
