from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

class Sith(models.Model):
    alert_msg = models.TextField(_("alert message"), default="", blank=True)
    info_msg = models.TextField(_("info message"), default="", blank=True)
    index_page = models.TextField(_("index page"), default="", blank=True)

    def is_owned_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)

    def __str__(self):
        return "⛩ Sith ⛩"

