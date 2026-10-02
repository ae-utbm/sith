# Register your models here.
from django.contrib import admin

from timetable.models import Timetable, TimetableSlot


class TimetableSlotInline(admin.TabularInline):
    model = TimetableSlot


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("user", "semester")
    search_fields = ("user__nick_name", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
    inlines = (TimetableSlotInline,)
    list_select_related = ("user",)
