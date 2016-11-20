from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

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
        return self.can_be_edited_by(user) or (self.is_in_sas and self.is_moderated and
                user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP))

    def get_download_url(self):
        return reverse('sas:download', kwargs={'picture_id': self.id})

    def get_download_compressed_url(self):
        return reverse('sas:download_compressed', kwargs={'picture_id': self.id})

    def get_download_thumb_url(self):
        return reverse('sas:download_thumb', kwargs={'picture_id': self.id})

    def get_next(self):
        return self.parent.children.exclude(is_moderated=False, asked_for_removal=True).filter(id__gt=self.id).order_by('id').first()

    def get_previous(self):
        return self.parent.children.exclude(is_moderated=False, asked_for_removal=True).filter(id__lt=self.id).order_by('id').last()

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
        return self.can_be_edited_by(user) or (self.is_in_sas and self.is_moderated and
                user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP))

    def get_absolute_url(self):
        return reverse('sas:album', kwargs={'album_id': self.id})

class PeoplePictureRelation(models.Model):
    """
    The PeoplePictureRelation class makes the connection between User and Picture

    """
    user = models.ForeignKey(User, verbose_name=_('user'), related_name="pictures", null=False, blank=False)
    picture = models.ForeignKey(Picture, verbose_name=_('picture'), related_name="people", null=False, blank=False)

    class Meta:
        unique_together = ['user', 'picture']
