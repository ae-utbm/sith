from django.contrib import admin

from reservation.models import ReservationSlot, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "club")
    list_filter = (("club", admin.RelatedOnlyFieldListFilter), "location")
    autocomplete_fields = ("club",)
    search_fields = ("name",)


@admin.register(ReservationSlot)
class ReservationSlotAdmin(admin.ModelAdmin):
    list_display = ("room", "start_at", "end_at", "author")
    autocomplete_fields = ("author",)
    list_filter = ("room",)
    date_hierarchy = "start_at"
