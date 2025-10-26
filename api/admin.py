from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from api.hashers import generate_key
from api.models import ApiClient, ApiKey


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "updated_at")
    search_fields = (
        "name",
        "owner__first_name",
        "owner__last_name",
        "owner__nick_name",
    )
    autocomplete_fields = ("owner", "groups", "client_permissions")
    readonly_fields = ("hmac_key",)
    actions = ("reset_hmac_key",)

    @admin.action(permissions=["change"], description=_("Reset HMAC key"))
    def reset_hmac_key(self, _request: HttpRequest, queryset: QuerySet[ApiClient]):
        objs = list(queryset)
        for obj in objs:
            obj.reset_hmac(commit=False)
        ApiClient.objects.bulk_update(objs, fields=["hmac_key"])


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "created_at", "revoked")
    list_filter = ("revoked",)
    date_hierarchy = "created_at"

    readonly_fields = ("prefix", "hashed_key")
    actions = ("revoke_keys",)

    def save_model(self, request: HttpRequest, obj: ApiKey, form, change):
        if not change:
            key, hashed = generate_key()
            obj.prefix = key[: ApiKey.PREFIX_LENGTH]
            obj.hashed_key = hashed
            self.message_user(
                request,
                _(
                    "The API key for %(name)s is: %(key)s. "
                    "Please store it somewhere safe: "
                    "you will not be able to see it again."
                )
                % {"name": obj.name, "key": key},
                level=messages.WARNING,
            )
        return super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj: ApiKey | None = None):
        if obj is None or obj.revoked:
            return ["revoked", *self.readonly_fields]
        return self.readonly_fields

    @admin.action(description=_("Revoke selected API keys"))
    def revoke_keys(self, _request: HttpRequest, queryset: QuerySet[ApiKey]):
        queryset.update(revoked=True)
