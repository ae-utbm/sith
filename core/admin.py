from django.contrib import admin
from core.models import User, Page, Group
from django.contrib.auth.models import Group as AuthGroup


admin.site.register(User)
admin.site.unregister(AuthGroup)
admin.site.register(Group)
admin.site.register(Page)

