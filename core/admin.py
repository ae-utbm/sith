from django.contrib import admin
from core.models import User, Page, RealGroup
from django.contrib.auth.models import Group as AuthGroup


admin.site.register(User)
admin.site.unregister(AuthGroup)
admin.site.register(RealGroup)
admin.site.register(Page)

