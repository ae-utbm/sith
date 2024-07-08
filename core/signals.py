from django.core.cache import cache
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from core.models import User


@receiver(m2m_changed, sender=User.groups.through, dispatch_uid="user_groups_changed")
def user_groups_changed(sender, instance: User, **kwargs):
    """
    Clear the cached groups of the user
    """
    # As a m2m relationship doesn't live within the model
    # but rather on an intermediary table, there is no
    # model method to override, meaning we must use
    # a signal to invalidate the cache when a user is removed from a group
    cache.delete(f"user_{instance.pk}_groups")
