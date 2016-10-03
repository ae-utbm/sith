from django.contrib import admin

from counter.models import *

# Register your models here.
admin.site.register(Customer)
admin.site.register(ProductType)
admin.site.register(Product)
admin.site.register(Counter)
admin.site.register(Refilling)
admin.site.register(Selling)
admin.site.register(Permanency)
admin.site.register(CashRegisterSummary)
admin.site.register(Eticket)

