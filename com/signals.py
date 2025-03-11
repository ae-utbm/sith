from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from com.ics_calendar import IcsCalendar
from com.models import News


@receiver([post_save, post_delete], sender=News, dispatch_uid="update_internal_ics")
def update_internal_ics(*args, **kwargs):
    _ = IcsCalendar.make_internal()
