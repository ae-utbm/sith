from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission

from core.models import Group

if TYPE_CHECKING:
    from core.models import User


class SithModelBackend(ModelBackend):
    """Custom auth backend for the Sith.

    In fact, it's the exact same backend as `django.contrib.auth.backend.ModelBackend`,
    with the exception that group permissions are fetched slightly differently.
    Indeed, django tries by default to fetch the permissions associated
    with all the `django.contrib.auth.models.Group` of a user ;
    however, our User model overrides that, so the actual linked group model
    is [core.models.Group][].
    Instead of having the relation `auth_perm --> auth_group <-- core_user`,
    we have `auth_perm --> auth_group <-- core_group <-- core_user`.

    Thus, this backend make the small tweaks necessary to make
    our custom models interact with the django auth.
    """

    def _get_group_permissions(self, user_obj: User):
        # union of querysets doesn't work if the queryset is ordered.
        # The empty `order_by` here are actually there to *remove*
        # any default ordering defined in managers or model Meta
        groups = user_obj.groups.order_by()
        if user_obj.is_subscribed:
            groups = groups.union(
                Group.objects.filter(pk=settings.SITH_GROUP_SUBSCRIBERS_ID).order_by()
            )
        return Permission.objects.filter(
            group__group__in=groups.values_list("pk", flat=True)
        )
