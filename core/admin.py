from django.contrib import admin
from ajax_select import make_ajax_form
from core.models import User, Page, RealGroup, SithFile
from django.contrib.auth.models import Group as AuthGroup


admin.site.register(User)
admin.site.unregister(AuthGroup)
admin.site.register(RealGroup)
admin.site.register(Page)

@admin.register(SithFile)
class SithFileAdmin(admin.ModelAdmin):
    form = make_ajax_form(SithFile, {
        'parent': 'files',  # ManyToManyField
        })
