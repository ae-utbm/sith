from django.db import models
from django.core.urlresolvers import reverse_lazy, reverse
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
    def is_vertical(self):
        with open((settings.MEDIA_ROOT + self.file.name).encode('utf-8'), 'rb') as f:
            im = Image.open(BytesIO(f.read()))
            (w, h) = im.size
            return (w / h) < 1
        return False

    def can_be_edited_by(self, user):
        file = SithFile.objects.filter(id=self.id).first()
        return user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID) or user.can_edit(file)

    def can_be_viewed_by(self, user):
        file = SithFile.objects.filter(id=self.id).first()
        return self.can_be_edited_by(user) or (self.is_in_sas and self.is_moderated and
                user.was_subscribed()) or user.can_view(file)

    def get_download_url(self):
        return reverse('sas:download', kwargs={'picture_id': self.id})

    def get_download_compressed_url(self):
        return reverse('sas:download_compressed', kwargs={'picture_id': self.id})

    def get_download_thumb_url(self):
        return reverse('sas:download_thumb', kwargs={'picture_id': self.id})

    def get_absolute_url(self):
        return reverse('sas:picture', kwargs={'picture_id': self.id})

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
            name = self.__getattribute__(attr).name
            with open((settings.MEDIA_ROOT + name).encode('utf-8'), 'r+b') as file:
                if file:
                    im = Image.open(BytesIO(file.read()))
                    file.seek(0)
                    im = im.rotate(degree, expand=True)
                    im.save(fp=file, format=self.mime_type.split('/')[-1].upper(), quality=90, optimize=True, progressive=True)

    def get_next(self):
        if self.is_moderated:
            return self.parent.children.filter(is_moderated=True, asked_for_removal=False, is_folder=False,
                    id__gt=self.id).order_by('id').first()
        else:
            return Picture.objects.filter(id__gt=self.id, is_moderated=False, is_in_sas=True).order_by('id').first()

    def get_previous(self):
        if self.is_moderated:
            return self.parent.children.filter(is_moderated=True, asked_for_removal=False, is_folder=False,
                    id__lt=self.id).order_by('id').last()
        else:
            return Picture.objects.filter(id__lt=self.id, is_moderated=False, is_in_sas=True).order_by('-id').first()

class Album(SithFile):
    class Meta:
        proxy = True

    def can_be_edited_by(self, user):
        file = SithFile.objects.filter(id=self.id).first()
        return user.is_in_group(settings.SITH_GROUP_SAS_ADMIN_ID) or user.can_edit(file)

    def can_be_viewed_by(self, user):
        file = SithFile.objects.filter(id=self.id).first()
        return self.can_be_edited_by(user) or (self.is_in_sas and self.is_moderated and
                user.was_subscribed()) or user.can_view(file)

    def get_absolute_url(self):
        return reverse('sas:album', kwargs={'album_id': self.id})

    def get_download_url(self):
        return reverse('sas:download', kwargs={'picture_id': self.id})

class PeoplePictureRelation(models.Model):
    """
    The PeoplePictureRelation class makes the connection between User and Picture

    """
    user = models.ForeignKey(User, verbose_name=_('user'), related_name="pictures", null=False, blank=False)
    picture = models.ForeignKey(Picture, verbose_name=_('picture'), related_name="people", null=False, blank=False)

    class Meta:
        unique_together = ['user', 'picture']

    def __str__(self):
        return self.user.get_display_name() + " - " + str(self.picture)
