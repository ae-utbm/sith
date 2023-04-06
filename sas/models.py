# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

import os
from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image

from core.models import SithFile, User
from core.utils import exif_auto_rotate, resize_image


class SASPictureManager(models.Manager):
    def get_queryset(self):
        return (
            super(SASPictureManager, self)
            .get_queryset()
            .filter(is_in_sas=True, is_folder=False)
        )


class SASAlbumManager(models.Manager):
    def get_queryset(self):
        return (
            super(SASAlbumManager, self)
            .get_queryset()
            .filter(is_in_sas=True, is_folder=True)
        )


class Picture(SithFile):
    class Meta:
        proxy = True

    objects = SASPictureManager()

    @property
    def is_vertical(self):
        with open(
            os.path.join(settings.MEDIA_ROOT, self.file.name).encode("utf-8"), "rb"
        ) as f:
            im = Image.open(BytesIO(f.read()))
            (w, h) = im.size
            return (w / h) < 1

    def can_be_edited_by(self, user):
        perm = cache.get("%d_can_edit_pictures" % (user.id), None)
        if perm is None:
            perm = user.is_root or user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID)

        cache.set("%d_can_edit_pictures" % (user.id), perm, timeout=4)
        return perm

    def can_be_viewed_by(self, user):
        # SAS pictures are visible to old subscribers
        # Result is cached 4s for this user
        if user.is_anonymous:
            return False

        perm = cache.get("%d_can_view_pictures" % (user.id), False)
        if not perm:
            perm = user.was_subscribed

        cache.set("%d_can_view_pictures" % (user.id), perm, timeout=4)
        return (perm and self.is_moderated and self.is_in_sas) or self.can_be_edited_by(
            user
        )

    def get_download_url(self):
        return reverse("sas:download", kwargs={"picture_id": self.id})

    def get_download_compressed_url(self):
        return reverse("sas:download_compressed", kwargs={"picture_id": self.id})

    def get_download_thumb_url(self):
        return reverse("sas:download_thumb", kwargs={"picture_id": self.id})

    def get_absolute_url(self):
        return reverse("sas:picture", kwargs={"picture_id": self.id})

    def generate_thumbnails(self, overwrite=False):
        im = Image.open(BytesIO(self.file.read()))
        try:
            im = exif_auto_rotate(im)
        except:
            pass
        file = resize_image(im, max(im.size), self.mime_type.split("/")[-1])
        thumb = resize_image(im, 200, self.mime_type.split("/")[-1])
        compressed = resize_image(im, 1200, self.mime_type.split("/")[-1])
        if overwrite:
            self.file.delete()
            self.thumbnail.delete()
            self.compressed.delete()
        self.file = file
        self.file.name = self.name
        self.thumbnail = thumb
        self.thumbnail.name = self.name
        self.compressed = compressed
        self.compressed.name = self.name
        self.save()

    def rotate(self, degree):
        for attr in ["file", "compressed", "thumbnail"]:
            name = self.__getattribute__(attr).name
            with open(
                os.path.join(settings.MEDIA_ROOT, name).encode("utf-8"), "r+b"
            ) as file:
                if file:
                    im = Image.open(BytesIO(file.read()))
                    file.seek(0)
                    im = im.rotate(degree, expand=True)
                    im.save(
                        fp=file,
                        format=self.mime_type.split("/")[-1].upper(),
                        quality=90,
                        optimize=True,
                        progressive=True,
                    )

    def get_next(self):
        if self.is_moderated:
            return (
                self.parent.children.filter(
                    is_moderated=True,
                    asked_for_removal=False,
                    is_folder=False,
                    id__gt=self.id,
                )
                .order_by("id")
                .first()
            )
        else:
            return (
                Picture.objects.filter(id__gt=self.id, is_moderated=False)
                .order_by("id")
                .first()
            )

    def get_previous(self):
        if self.is_moderated:
            return (
                self.parent.children.filter(
                    is_moderated=True,
                    asked_for_removal=False,
                    is_folder=False,
                    id__lt=self.id,
                )
                .order_by("id")
                .last()
            )
        else:
            return (
                Picture.objects.filter(id__lt=self.id, is_moderated=False)
                .order_by("-id")
                .first()
            )


class Album(SithFile):
    class Meta:
        proxy = True

    objects = SASAlbumManager()

    @property
    def children_pictures(self):
        return Picture.objects.filter(parent=self)

    @property
    def children_albums(self):
        return Album.objects.filter(parent=self)

    def can_be_edited_by(self, user):
        return user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID)

    def can_be_viewed_by(self, user):
        # file = SithFile.objects.filter(id=self.id).first()
        return self.can_be_edited_by(user) or (
            self.is_in_sas and self.is_moderated and user.was_subscribed
        )  # or user.can_view(file)

    def get_absolute_url(self):
        return reverse("sas:album", kwargs={"album_id": self.id})

    def get_download_url(self):
        return reverse("sas:album_preview", kwargs={"album_id": self.id})

    def generate_thumbnail(self):
        p = (
            self.children_pictures.order_by("?").first()
            or self.children_albums.exclude(file=None)
            .exclude(file="")
            .order_by("?")
            .first()
        )
        if p and p.file:
            im = Image.open(BytesIO(p.file.read()))
            self.file = resize_image(im, 200, "jpeg")
            self.file.name = self.name + "/thumb.jpg"
            self.save()


def sas_notification_callback(notif):
    count = Picture.objects.filter(is_moderated=False).count()
    if count:
        notif.viewed = False
    else:
        notif.viewed = True
    notif.param = "%s" % count
    notif.date = timezone.now()


class PeoplePictureRelation(models.Model):
    """
    The PeoplePictureRelation class makes the connection between User and Picture

    """

    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        related_name="pictures",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    picture = models.ForeignKey(
        Picture,
        verbose_name=_("picture"),
        related_name="people",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ["user", "picture"]

    def __str__(self):
        return self.user.get_display_name() + " - " + str(self.picture)
