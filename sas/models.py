from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.files.base import ContentFile

from PIL import Image
from io import BytesIO

from core.models import SithFile, User
from core.utils import resize_image, exif_auto_rotate

class Picture(SithFile):
    class Meta:
        proxy = True

    @property
    def is_in_sas(self):
        sas = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        return sas in self.get_parent_list()

    @property
    def is_vertical(self):
        im = Image.open(BytesIO(self.file.read()))
        (w, h) = im.size
        return (w / h) < 1

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

    def generate_thumbnails(self):
        im = Image.open(BytesIO(self.file.read()))
        try:
            im = exif_auto_rotate(im)
        except: pass
        file = resize_image(im, max(im.size), self.mime_type.split('/')[-1])
        thumb = resize_image(im, 200, self.mime_type.split('/')[-1])
        compressed = resize_image(im, 600, self.mime_type.split('/')[-1])
        self.file = file
        self.file.name = self.name
        self.thumbnail = thumb
        self.thumbnail.name = self.name
        self.compressed = compressed
        self.compressed.name = self.name
        self.save()

    def rotate(self, degree):
        for attr in ['file', 'compressed', 'thumbnail']:
            if self.__getattribute__(attr):
                im = Image.open(BytesIO(self.__getattribute__(attr).read()))
                new_image = BytesIO()
                im = im.rotate(degree, expand=True)
                im.save(fp=new_image, format=self.mime_type.split('/')[-1].upper(), quality=90, optimize=True, progressive=True)
                self.__getattribute__(attr).save(self.name, ContentFile(new_image.getvalue()))
                self.save()

    def get_next(self):
        return self.parent.children.filter(is_moderated=True, asked_for_removal=False, is_folder=False,
                id__gt=self.id).order_by('id').first()

    def get_previous(self):
        return self.parent.children.filter(is_moderated=True, asked_for_removal=False, is_folder=False,
                id__lt=self.id).order_by('id').last()

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
