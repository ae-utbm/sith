from typing import Iterable

from django.contrib.auth.models import Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from core.models import Group, User


class ApiClient(models.Model):
    name = models.CharField(_("name"), max_length=64)
    owner = models.ForeignKey(
        User,
        verbose_name=_("owner"),
        related_name="api_clients",
        on_delete=models.CASCADE,
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        related_name="api_clients",
    )
    client_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("client permissions"),
        blank=True,
        help_text=_("Specific permissions for this api client."),
        related_name="clients",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _perm_cache: set[str] | None = None

    class Meta:
        verbose_name = _("api client")
        verbose_name_plural = _("api clients")

    def __str__(self):
        return self.name

    def has_perm(self, perm: str):
        """Return True if the client has the specified permission."""

        if self._perm_cache is None:
            group_permissions = (
                Permission.objects.filter(group__group__in=self.groups.all())
                .values_list("content_type__app_label", "codename")
                .order_by()
            )
            client_permissions = self.client_permissions.values_list(
                "content_type__app_label", "codename"
            ).order_by()
            self._perm_cache = {
                f"{content_type}.{name}"
                for content_type, name in (*group_permissions, *client_permissions)
            }
        return perm in self._perm_cache

    def has_perms(self, perm_list):
        """
        Return True if the client has each of the specified permissions. If
        object is passed, check if the client has all required perms for it.
        """
        if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")
        return all(self.has_perm(perm) for perm in perm_list)


class ApiKey(models.Model):
    PREFIX_LENGTH = 5

    name = models.CharField(_("name"), blank=True, default="")
    prefix = models.CharField(_("prefix"), max_length=PREFIX_LENGTH, editable=False)
    hashed_key = models.CharField(
        _("hashed key"), max_length=150, db_index=True, editable=False
    )
    client = models.ForeignKey(
        ApiClient,
        verbose_name=_("api client"),
        related_name="api_keys",
        on_delete=models.CASCADE,
    )
    revoked = models.BooleanField(pgettext_lazy("api key", "revoked"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("api key")
        verbose_name_plural = _("api keys")
        permissions = [("revoke_apikey", "Revoke API keys")]

    def __str__(self):
        return f"{self.name} ({self.prefix}***)"
