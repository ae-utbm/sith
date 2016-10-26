from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse

from core.models import SithFile, User

class Picture(SithFile):
    class Meta:
        proxy = True

    @property
    def is_in_sas(self):
        sas = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        return sas in self.get_parent_list()

    def can_be_edited_by(self, user):
        return user.is_in_group(settings.SITH_SAS_ADMIN_GROUP_ID)

    def can_be_viewed_by(self, user):
        return self.can_be_edited_by(user) or (self.is_in_sas and self.is_authorized and
                user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP))

    def get_download_url(self):
        return reverse('sas:download', kwargs={'picture_id': self.id})

class Album(SithFile):
    class Meta:
        proxy = True

    @property
    def is_in_sas(self):
        sas = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        return sas in self.get_parent_list()

    def can_be_edited_by(self, user):
        return user.is_in_group(settings.SITH_SAS_ADMIN_GROUP_ID)

    def can_be_viewed_by(self, user):
        return self.can_be_edited_by(user) or (self.is_in_sas and self.is_authorized and
                user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP))

    def get_absolute_url(self):
        return reverse('sas:album', kwargs={'album_id': self.id})

