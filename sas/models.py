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

import contextlib
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Self

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.db.models.deletion import Collector
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from PIL import Image

from core.models import Group, Notification, User
from core.utils import exif_auto_rotate, resize_image

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile


def get_directory(instance: SasFile, filename: str):
    return f"./{instance.parent_path}/{filename}"


def get_compressed_directory(instance: SasFile, filename: str):
    return f"./.compressed/{instance.parent_path}/{filename}"


def get_thumbnail_directory(instance: SasFile, filename: str):
    if isinstance(instance, Album):
        _, extension = filename.rsplit(".", 1)
        filename = f"{instance.name}/thumb.{extension}"
    return f"./.thumbnails/{instance.parent_path}/{filename}"


class SasFile(models.Model):
    """Abstract model for SAS files

    May be used to have logic that should be shared by both
    [Picture][sas.models.Picture] and [Album][sas.models.Album].
    """

    class Meta:
        abstract = True
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

    @cached_property
    def parent_path(self) -> str:
        """The parent location in the SAS album tree (e.g. `SAS/foo/bar`)."""
        return "/".join(["SAS", *[p.name for p in self.parent_list]])

    @cached_property
    def parent_list(self) -> list[Album]:
        """The ancestors of this SAS object.

        The result is ordered from the direct parent to the farthest one.
        """
        parents = []
        current = self.parent
        while current is not None:
            parents.append(current)
            current = current.parent
        return parents


class AlbumQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        """Filter the albums that this user can view.

        Warning:
            Calling this queryset method may add several additional requests.
        """
        if user.is_root or user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            return self.all()
        if user.was_subscribed:
            return self.filter(is_moderated=True)
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


class Album(SasFile):
    NAME_MAX_LENGTH: ClassVar[int] = 50

    name = models.CharField(_("name"), max_length=100)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        verbose_name=_("parent"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    thumbnail = models.FileField(
        upload_to=get_thumbnail_directory,
        verbose_name=_("thumbnail"),
        max_length=256,
        blank=True,
    )
    view_groups = models.ManyToManyField(
        Group, related_name="viewable_albums", verbose_name=_("view groups"), blank=True
    )
    edit_groups = models.ManyToManyField(
        Group, related_name="editable_albums", verbose_name=_("edit groups"), blank=True
    )
    event_date = models.DateField(
        _("event date"),
        help_text=_("The date on which the photos in this album were taken"),
        default=timezone.localdate,
        blank=True,
    )
    is_moderated = models.BooleanField(_("is moderated"), default=False)

    objects = AlbumQuerySet.as_manager()

    class Meta:
        verbose_name = _("album")
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"],
                name="unique_album_name_if_same_parent",
                # TODO : add `nulls_distinct=True` after upgrading to django>=5.0
            )
        ]

    def __str__(self):
        return f"Album {self.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for user in User.objects.filter(
            groups__id__in=[settings.SITH_GROUP_SAS_ADMIN_ID]
        ):
            Notification(
                user=user,
                url=reverse("sas:moderation"),
                type="SAS_MODERATION",
                param="1",
            ).save()

    def get_absolute_url(self):
        return reverse("sas:album", kwargs={"album_id": self.id})

    def clean(self):
        super().clean()
        if "/" in self.name:
            raise ValidationError(_("Character '/' not authorized in name"))
        if self.parent_id is not None and (
            self.id == self.parent_id or self in self.parent_list
        ):
            raise ValidationError(_("Loop in album tree"), code="loop")
        if self.thumbnail:
            try:
                Image.open(BytesIO(self.thumbnail.read()))
            except Image.UnidentifiedImageError as e:
                raise ValidationError(_("This is not a valid album thumbnail")) from e

    def delete(self, *args, **kwargs):
        """Delete the album, all of its children and all linked disk files"""
        collector = Collector(using="default")
        collector.collect([self])
        albums: set[Album] = collector.data[Album]
        pictures: set[Picture] = collector.data[Picture]
        files: list[FieldFile] = [
            *[a.thumbnail for a in albums],
            *[p.thumbnail for p in pictures],
            *[p.compressed for p in pictures],
            *[p.original for p in pictures],
        ]
        # `bool(f)` checks that the file actually exists on the disk
        files = [f for f in files if bool(f)]
        folders = {Path(f.path).parent for f in files}
        res = super().delete(*args, **kwargs)
        # once the model instances have been deleted,
        # delete the actual files.
        for file in files:
            # save=False ensures that django doesn't recreate the db record,
            # which would make the whole deletion pointless
            # cf. https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.fields.files.FieldFile.delete
            file.delete(save=False)
        for folder in folders:
            # now that the files are deleted, remove the empty folders
            if folder.is_dir() and next(folder.iterdir(), None) is None:
                folder.rmdir()
        return res

    def get_download_url(self):
        return reverse("sas:album_preview", kwargs={"album_id": self.id})

    def generate_thumbnail(self):
        p = (
            self.pictures.exclude(thumbnail="").order_by("?").first()
            or self.children.exclude(thumbnail="").order_by("?").first()
        )
        if p:
            # The file is loaded into memory to duplicate it.
            # It may not be the most efficient way, but thumbnails are
            # usually quite small, so it's still ok
            self.thumbnail = ContentFile(p.thumbnail.read(), name="thumb.webp")
            self.save()


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


class Picture(SasFile):
    name = models.CharField(_("file name"), max_length=256)
    parent = models.ForeignKey(
        Album,
        related_name="pictures",
        verbose_name=_("album"),
        on_delete=models.CASCADE,
    )
    thumbnail = models.FileField(
        upload_to=get_thumbnail_directory,
        verbose_name=_("thumbnail"),
        max_length=256,
        unique=True,
    )
    original = models.FileField(
        upload_to=get_directory,
        verbose_name=_("original image"),
        max_length=256,
        unique=True,
    )
    compressed = models.FileField(
        upload_to=get_compressed_directory,
        verbose_name=_("compressed image"),
        max_length=256,
        unique=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(
        User,
        related_name="owned_pictures",
        verbose_name=_("owner"),
        on_delete=models.PROTECT,
    )

    is_moderated = models.BooleanField(_("is moderated"), default=False)
    asked_for_removal = models.BooleanField(_("asked for removal"), default=False)
    moderator = models.ForeignKey(
        User,
        related_name="moderated_pictures",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = PictureQuerySet.as_manager()

    class Meta:
        verbose_name = _("picture")
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"], name="sas_picture_unique_per_album"
            )
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("sas:picture", kwargs={"picture_id": self.id})

    def get_download_url(self):
        return reverse("sas:download", kwargs={"picture_id": self.id})

    def get_download_compressed_url(self):
        return reverse("sas:download_compressed", kwargs={"picture_id": self.id})

    def get_download_thumb_url(self):
        return reverse("sas:download_thumb", kwargs={"picture_id": self.id})

    @property
    def is_vertical(self):
        # original, compressed and thumbnail image have all three the same ratio,
        # so the smallest one is used to tell if the image is vertical
        im = Image.open(BytesIO(self.thumbnail.read()))
        (w, h) = im.size
        return w < h

    def generate_thumbnails(self):
        im = Image.open(self.original)
        with contextlib.suppress(Exception):
            im = exif_auto_rotate(im)
        # convert the compressed image and the thumbnail into webp
        # the HD version of the image doesn't need to be optimized, because :
        # - it isn't frequently queried
        # - optimizing large images takes a lot of time, which greatly hinders the UX
        # - photographers usually already optimize their images
        thumb = resize_image(im, 200, "webp")
        compressed = resize_image(im, 1200, "webp")
        new_extension_name = str(Path(self.original.name).with_suffix(".webp"))
        self.thumbnail = thumb
        self.thumbnail.name = new_extension_name
        self.compressed = compressed
        self.compressed.name = new_extension_name

    def rotate(self, degree):
        for field in self.original, self.compressed, self.thumbnail:
            with open(field.file, "r+b") as file:
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


def sas_notification_callback(notif: Notification):
    count = Picture.objects.filter(is_moderated=False).count()
    notif.viewed = not bool(count)
    notif.param = str(count)


class PeoplePictureRelationQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        if user.is_root or user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            return self
        if user.was_subscribed:
            return self.filter(Q(user_id=user.id) | Q(user__is_viewable=True))
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
