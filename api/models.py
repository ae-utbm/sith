import secrets
from typing import Iterable

from django.contrib.auth.models import Permission
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from core.models import Group, User


def get_hmac_key():
    return secrets.token_hex(64)


class ApiClient(models.Model):
    name = models.CharField(_("name"), max_length=64)
    owner = models.ForeignKey(
        User,
        verbose_name=_("owner"),
        related_name="api_clients",
        on_delete=models.CASCADE,
    )
    groups = models.ManyToManyField(
        Group, verbose_name=_("groups"), related_name="api_clients", blank=True
    )
    client_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("client permissions"),
        blank=True,
        help_text=_("Specific permissions for this api client."),
        related_name="clients",
    )
    hmac_key = models.CharField(_("HMAC Key"), max_length=128, default=get_hmac_key)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("api client")
        verbose_name_plural = _("api clients")

    def __str__(self):
        return self.name

    @cached_property
    def all_permissions(self) -> set[str]:
        permissions = (
            Permission.objects.filter(
                Q(group__group__in=self.groups.all()) | Q(clients=self)
            )
            .values_list("content_type__app_label", "codename")
            .order_by()
        )
        return {f"{content_type}.{name}" for content_type, name in permissions}

    def has_perm(self, perm: str):
        """Return True if the client has the specified permission."""
        return perm in self.all_permissions

    def has_perms(self, perm_list: Iterable[str]) -> bool:
        """Return True if the client has each of the specified permissions."""
        if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")
        return all(self.has_perm(perm) for perm in perm_list)

    def reset_hmac(self, *, commit: bool = True) -> str:
        """Reset and return the HMAC key for this client.

        Args:
            commit: if True (the default), persist the new hmac in db.
        """
        self.hmac_key = get_hmac_key()
        if commit:
            self.save()
        return self.hmac_key


class ApiKey(models.Model):
    PREFIX_LENGTH = 5
    KEY_LENGTH = 72
    HASHED_KEY_LENGTH = 136

    name = models.CharField(_("name"), blank=True, default="")
    prefix = models.CharField(_("prefix"), max_length=PREFIX_LENGTH, editable=False)
    hashed_key = models.CharField(
        _("hashed key"), max_length=HASHED_KEY_LENGTH, db_index=True, editable=False
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
