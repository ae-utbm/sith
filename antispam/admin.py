from django.contrib import admin

from antispam.models import ToxicDomain


@admin.register(ToxicDomain)
class ToxicDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "is_externally_managed", "created")
    search_fields = ("domain", "is_externally_managed", "created")
    list_filter = ("is_externally_managed",)
