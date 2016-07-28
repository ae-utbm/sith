from django.contrib import admin

from launderette.models import *

# Register your models here.
admin.site.register(Launderette)
admin.site.register(Machine)
admin.site.register(Token)
admin.site.register(Slot)
