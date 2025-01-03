from django.db.models.base import post_save
from django.dispatch import receiver

from com.models import IcsCalendar, News


@receiver(post_save, sender=News, dispatch_uid="update_internal_ics")
def update_internal_ics(*args, **kwargs):
    _ = IcsCalendar.make_internal()
