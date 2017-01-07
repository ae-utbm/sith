from django.contrib import admin

from stock.models import Stock, StockItem, ShoppingList, ShoppingListItem

# Register your models here.
admin.site.register(Stock)
admin.site.register(StockItem)
admin.site.register(ShoppingList)
admin.site.register(ShoppingListItem)