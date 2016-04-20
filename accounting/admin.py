from django.contrib import admin

from accounting.models import *


admin.site.register(Customer)
admin.site.register(ProductType)
admin.site.register(Product)
admin.site.register(BankAccount)
admin.site.register(ClubAccount)
admin.site.register(GeneralJournal)
admin.site.register(Operation)


