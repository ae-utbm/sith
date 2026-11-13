from django.contrib import admin

from stock.models import Stock, StockAction, StockItem, StockItemAction, StockItemStock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "can_be_view_by_board", "created_at", "updated_at")
    search_fields = ("name",)
    autocomplete_fields = ("club",)


@admin.register(StockAction)
class StockActionAdmin(admin.ModelAdmin):
    list_display = ("action", "comment", "user", "created_at")
    search_fields = ("action",)
    autocomplete_fields = ("user",)


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "is_hidden",
        "is_allow_negative",
        "created_at",
    )
    search_fields = ("name",)


@admin.register(StockItemStock)
class StockItemStockAdmin(admin.ModelAdmin):
    list_display = ("stock", "item", "quantity")
    autocomplete_fields = ("stock", "item")


@admin.register(StockItemAction)
class StockItemActionAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "item",
        "quantity_before",
        "quantity_after",
    )
    search_fields = ("item",)
