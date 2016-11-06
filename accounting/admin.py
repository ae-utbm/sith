from django.contrib import admin

from accounting.models import *


admin.site.register(BankAccount)
admin.site.register(ClubAccount)
admin.site.register(GeneralJournal)
admin.site.register(AccountingType)
admin.site.register(SimplifiedAccountingType)
admin.site.register(Operation)
admin.site.register(Label)
admin.site.register(Company)


