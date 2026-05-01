#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import ClassVar, Self

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image

from core.models import Notification, SithFile, User
from core.utils import resize_image


class SasFile(SithFile):
    """Proxy model for any file in the SAS.

    May be used to have logic that should be shared by both
    [Picture][sas.models.Picture] and [Album][sas.models.Album].
    """

    class Meta:
        proxy = True
        permissions = [
            ("moderate_sasfile", "Can moderate SAS files"),
            ("view_unmoderated_sasfile", "Can view not moderated SAS files"),
        ]

    def can_be_viewed_by(self, user):
        if user.is_anonymous:
            return False
        cache_key = (
            f"sas:{self._meta.model_name}_viewable_by_{user.id}_in_{self.parent_id}"
        )
        viewable: list[int] | None = cache.get(cache_key)
        if viewable is None:
            viewable = list(
                self.__class__.objects.filter(parent_id=self.parent_id)
                .viewable_by(user)
                .values_list("pk", flat=True)
            )
            cache.set(cache_key, viewable, timeout=10)
        return self.id in viewable

    def can_be_edited_by(self, user):
        return user.has_perm("sas.change_sasfile")


class PictureQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        """Filter the pictures that this user can view.

        Warning:
            Calling this queryset method may add several additional requests.
        """
        if user.has_perm("sas.moderate_sasfile"):
            return self.all()
        if user.was_subscribed:
            return self.filter(Q(is_moderated=True) | Q(owner=user))
        return self.filter(people__user_id=user.id, is_moderated=True)


class SASPictureManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_in_sas=True, is_folder=False)


class Picture(SasFile):
    class Meta:
        proxy = True

    objects = SASPictureManager.from_queryset(PictureQuerySet)()

    def get_download_url(self):
        return reverse(
            "sas:download",
            kwargs={"picture_id": self.id},
            query={"date": int(self.updated_at.timestamp())},
        )

    def get_download_compressed_url(self):
        return reverse(
            "sas:download_compressed",
            kwargs={"picture_id": self.id},
            query={"date": int(self.updated_at.timestamp())},
        )

    def get_download_thumb_url(self):
        return reverse(
            "sas:download_thumb",
            kwargs={"picture_id": self.id},
            query={"date": int(self.updated_at.timestamp())},
        )

    def get_absolute_url(self):
        return reverse("sas:picture", kwargs={"picture_id": self.id})

    def generate_thumbnails(
        self, *, img: Image.Image | None = None, save: bool = False
    ):
        """Generate the thumbnail and the compressed version of this picture.

        Args:
            img: if given, this will be used to generate
            all three images (file, compressed, thumbnail).
            Else, `self.file` will be used
            save: if True, save the instance in database.
        """
        img = img or Image.open(self.file)
        extension = self.mime_type.split("/")[-1]
        previous_files = [
            f.name for f in (self.file, self.thumbnail, self.compressed) if f
        ]
        # convert the compressed image and the thumbnail into webp
        # The original image keeps its original type, because it's not
        # meant to be shown on the website, but rather to keep the real image
        # for less frequent cases (like downloading the pictures of a user)
        # the HD version of the image doesn't need to be optimized, because :
        # - it isn't frequently queried
        # - optimizing large images takes a lot of time, which greatly hinders the UX
        # - photographers usually already optimize their images
        new_extension_name = str(Path(self.name).with_suffix(".webp"))
        file = resize_image(img, max(img.size), extension, optimize=False)
        self.file.save(self.name, file, save=False)
        thumbnail = resize_image(img, 200, "webp")
        self.thumbnail.save(new_extension_name, thumbnail, save=False)
        compressed = resize_image(img, 1200, "webp")
        self.compressed.save(new_extension_name, compressed, save=save)
        # once the new images have been saved, delete the previous ones.
        # The deletion of old files is done after, so that if anything goes
        # during the whole process, no data will be lost.
        for filename in previous_files:
            self.file.storage.delete(filename)

    def rotate(self, degree: int | float):
        """Rotate this picture and update its thumbnails accordingly.

        Args:
            degree: the rotation angle, in degree, counter-clockwise
        """
        img = Image.open(self.file).rotate(degree)
        self.generate_thumbnails(img=img, save=True)


class AlbumQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        """Filter the albums that this user can view.

        Warning:
            Calling this queryset method may add several additional requests.
        """
        if user.has_perm("sas.moderate_sasfile"):
            return self.all()
        if user.was_subscribed:
            return self.filter(Q(is_moderated=True) | Q(owner=user))
        # known bug : if all children of an album are also albums
        # then this album is excluded, even if one of the sub-albums should be visible.
        # The fs-like navigation is likely to be half-broken for non-subscribers,
        # but that's ok, since non-subscribers are expected to see only the albums
        # containing pictures on which they have been identified (hence, very few).
        # Most, if not all, of their albums will be displayed on the
        # `latest albums` section of the SAS.
        # Moreover, they will still see all of their picture in their profile.
        return self.filter(
            Exists(Picture.objects.filter(parent_id=OuterRef("pk")).viewable_by(user))
        )


class SASAlbumManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_in_sas=True, is_folder=True)


class Album(SasFile):
    NAME_MAX_LENGTH: ClassVar[int] = 50
    """Maximum length of an album's name.
    
    [SithFile][core.models.SithFile] have a maximum length
    of 256 characters.
    However, this limit is too high for albums.
    Names longer than 50 characters are harder to read
    and harder to display on the SAS page.
    
    It is to be noted, though, that this does not
    add or modify any db behaviour.
    It's just a constant to be used in views and forms.
    """

    class Meta:
        proxy = True

    objects = SASAlbumManager.from_queryset(AlbumQuerySet)()

    @property
    def children_pictures(self):
        return Picture.objects.filter(parent=self)

    @property
    def children_albums(self):
        return Album.objects.filter(parent=self)

    def get_absolute_url(self):
        if self.id == settings.SITH_SAS_ROOT_DIR_ID:
            return reverse("sas:main")
        return reverse("sas:album", kwargs={"album_id": self.id})

    def get_download_url(self):
        return reverse(
            "sas:album_preview",
            kwargs={"album_id": self.id},
            query={"date": int(self.updated_at.timestamp())},
        )

    def generate_thumbnail(self):
        p = self.children_pictures.order_by("?").first()
        if p and p.thumbnail:
            image = ContentFile(
                name=str(Path(self.name) / "thumb.webp"), content=p.thumbnail.read()
            )
            self.file = image
            self.save()


def sas_notification_callback(notif: Notification):
    count = Picture.objects.filter(is_moderated=False).count()
    notif.viewed = not bool(count)
    notif.param = str(count)


class PeoplePictureRelationQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        if user.is_root or user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            return self
        if user.was_subscribed:
            return self.filter(
                Q(user_id=user.id)
                | Q(user__is_viewable=True)
                | Q(user__whitelisted_users=user)
            )
        return self.filter(user_id=user.id)


class PeoplePictureRelation(models.Model):
    """The PeoplePictureRelation class makes the connection between User and Picture."""

    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        related_name="pictures",
        on_delete=models.CASCADE,
    )
    picture = models.ForeignKey(
        Picture,
        verbose_name=_("picture"),
        related_name="people",
        on_delete=models.CASCADE,
    )

    objects = PeoplePictureRelationQuerySet.as_manager()

    class Meta:
        unique_together = ["user", "picture"]

    def __str__(self):
        return f"Moderation request by {self.user.get_short_name()} - {self.picture}"


class PictureModerationRequest(models.Model):
    """A request to remove a Picture from the SAS."""

    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name=_("Author"),
        related_name="moderation_requests",
        on_delete=models.CASCADE,
    )
    picture = models.ForeignKey(
        Picture,
        verbose_name=_("Picture"),
        related_name="moderation_requests",
        on_delete=models.CASCADE,
    )
    reason = models.TextField(
        verbose_name=_("Reason"),
        default="",
        help_text=_("Why do you want this image to be removed ?"),
    )

    class Meta:
        verbose_name = _("Picture moderation request")
        verbose_name_plural = _("Picture moderation requests")
        constraints = [
            models.UniqueConstraint(
                fields=["author", "picture"], name="one_request_per_user_per_picture"
            )
        ]

    def __str__(self):
        return f"Moderation request by {self.author.get_short_name()}"
