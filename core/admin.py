from django.contrib import admin
from core.models import User, Page, Group


admin.site.register(User)
admin.site.register(Group)
admin.site.register(Page)

