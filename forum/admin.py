from django.contrib import admin

from forum.models import *

admin.site.register(Forum)
admin.site.register(ForumTopic)
admin.site.register(ForumMessage)
