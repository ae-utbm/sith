from django.contrib import admin
from .models import User, Page, Group


admin.site.register(User)
admin.site.register(Group)
admin.site.register(Page)

