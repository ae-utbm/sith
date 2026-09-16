from __future__ import annotations

import typing

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from django.db.models import Exists, OuterRef, Q, QuerySet

from core.models import Group, User

if typing.TYPE_CHECKING:
    from django.db.models.base import Model


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

    @typing.override
    def with_perm(
        self,
        perm: str | Permission,
        is_active: bool | None = True,
        include_superusers: bool = False,
        obj: Model | None = None,
    ) -> QuerySet[User]:
        """Return users that have permission "perm".

        Contrary to the base django method, superusers aren't included in the
        result.
        This is because the OR operation to include superusers in the query result
        utterly destroy the query performances on postgres
        (it makes it like 1000x slower, and I'm not even kidding).
        To overcome that, we could use a UNION instead, but then we wouldn't
        be able to perform further filter operations on the queryset.
        Thus, the `include_superusers` argument is not used at all.

        Because of that, it is useless to set `include_superusers`,
        as it will be silently ignored.
        The only reason it's still there is not to break the interface
        of the base class.
        """
        if isinstance(perm, str):
            try:
                app_label, codename = perm.split(".")
            except ValueError as e:
                raise ValueError(
                    "Permission name should be in the form "
                    "app_label.permission_codename."
                ) from e
            permission_q = Q(codename=codename, content_type__app_label=app_label)
        elif isinstance(perm, Permission):
            permission_q = Q(pk=perm.pk)
        else:
            raise TypeError(
                "The `perm` argument must be a string or a permission instance."
            )

        user_q = Exists(
            Permission.objects.filter(
                Q(group__group__users=OuterRef("pk")) | Q(user=OuterRef("pk")),
                permission_q,
            )
        )
        if is_active is not None:
            user_q &= Q(is_active=is_active)
        return User.objects.filter(user_q)
