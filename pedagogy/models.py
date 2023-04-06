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

from django.conf import settings
from django.core import validators
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import User

# Create your models here.


class UV(models.Model):
    """
    Contains infos about an UV (course)
    """

    code = models.CharField(
        _("code"),
        max_length=10,
        unique=True,
        validators=[
            validators.RegexValidator(
                regex="([A-Z0-9]+)",
                message=_(
                    "The code of an UV must only contains uppercase characters without accent and numbers"
                ),
            )
        ],
    )
    author = models.ForeignKey(
        User,
        related_name="uv_created",
        verbose_name=_("author"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    credit_type = models.CharField(
        _("credit type"),
        max_length=10,
        choices=settings.SITH_PEDAGOGY_UV_TYPE,
        default=settings.SITH_PEDAGOGY_UV_TYPE[0][0],
    )
    manager = models.CharField(_("uv manager"), max_length=300)
    semester = models.CharField(
        _("semester"),
        max_length=20,
        choices=settings.SITH_PEDAGOGY_UV_SEMESTER,
        default=settings.SITH_PEDAGOGY_UV_SEMESTER[0][0],
    )
    language = models.CharField(
        _("language"),
        max_length=10,
        choices=settings.SITH_PEDAGOGY_UV_LANGUAGE,
        default=settings.SITH_PEDAGOGY_UV_LANGUAGE[0][0],
    )
    credits = models.IntegerField(
        _("credits"),
        validators=[validators.MinValueValidator(0)],
        blank=False,
        null=False,
    )
    # Double star type not implemented yet

    department = models.CharField(
        _("departmenmt"),
        max_length=10,
        choices=settings.SITH_PROFILE_DEPARTMENTS,
        default=settings.SITH_PROFILE_DEPARTMENTS[-1][0],
    )

    # All texts about the UV
    title = models.CharField(_("title"), max_length=300)
    manager = models.CharField(_("uv manager"), max_length=300)
    objectives = models.TextField(_("objectives"))
    program = models.TextField(_("program"))
    skills = models.TextField(_("skills"))
    key_concepts = models.TextField(_("key concepts"))

    # Hours types CM, TD, TP, THE and TE
    # Kind of dirty but I have nothing else in mind for now
    hours_CM = models.IntegerField(
        _("hours CM"),
        validators=[validators.MinValueValidator(0)],
        blank=False,
        null=False,
        default=0,
    )
    hours_TD = models.IntegerField(
        _("hours TD"),
        validators=[validators.MinValueValidator(0)],
        blank=False,
        null=False,
        default=0,
    )
    hours_TP = models.IntegerField(
        _("hours TP"),
        validators=[validators.MinValueValidator(0)],
        blank=False,
        null=False,
        default=0,
    )
    hours_THE = models.IntegerField(
        _("hours THE"),
        validators=[validators.MinValueValidator(0)],
        blank=False,
        null=False,
        default=0,
    )
    hours_TE = models.IntegerField(
        _("hours TE"),
        validators=[validators.MinValueValidator(0)],
        blank=False,
        null=False,
        default=0,
    )

    def is_owned_by(self, user):
        """
        Can be created by superuser, root or pedagogy admin user
        """
        return user.is_in_group(pk=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)

    def can_be_viewed_by(self, user):
        """
        Only visible by subscribers
        """
        return user.is_subscribed

    def __grade_average_generic(self, field):
        comments = self.comments.filter(**{field + "__gte": 0})
        if not comments.exists():
            return -1

        return int(sum(comments.values_list(field, flat=True)) / comments.count())

    def get_absolute_url(self):
        return reverse("pedagogy:uv_detail", kwargs={"uv_id": self.id})

    def has_user_already_commented(self, user):
        """
        Help prevent multiples comments from the same user
        This function checks that no other comment has been posted by a specified user

        :param user: core.models.User
        :return: if the user has already posted a comment on this UV
        :rtype: bool
        """
        return self.comments.filter(author=user).exists()

    @cached_property
    def grade_global_average(self):
        return self.__grade_average_generic("grade_global")

    @cached_property
    def grade_utility_average(self):
        return self.__grade_average_generic("grade_utility")

    @cached_property
    def grade_interest_average(self):
        return self.__grade_average_generic("grade_interest")

    @cached_property
    def grade_teaching_average(self):
        return self.__grade_average_generic("grade_teaching")

    @cached_property
    def grade_work_load_average(self):
        return self.__grade_average_generic("grade_work_load")

    def __str__(self):
        return self.code


class UVComment(models.Model):
    """
    A comment about an UV
    """

    author = models.ForeignKey(
        User,
        related_name="uv_comments",
        verbose_name=_("author"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    uv = models.ForeignKey(
        UV, related_name="comments", verbose_name=_("uv"), on_delete=models.CASCADE
    )
    comment = models.TextField(_("comment"), blank=True)
    grade_global = models.IntegerField(
        _("global grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        blank=False,
        null=False,
        default=-1,
    )
    grade_utility = models.IntegerField(
        _("utility grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        blank=False,
        null=False,
        default=-1,
    )
    grade_interest = models.IntegerField(
        _("interest grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        blank=False,
        null=False,
        default=-1,
    )
    grade_teaching = models.IntegerField(
        _("teaching grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        blank=False,
        null=False,
        default=-1,
    )
    grade_work_load = models.IntegerField(
        _("work load grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        blank=False,
        null=False,
        default=-1,
    )
    publish_date = models.DateTimeField(_("publish date"), blank=True)

    def is_owned_by(self, user):
        """
        Is owned by a pedagogy admin, a superuser or the author himself
        """
        return self.author == user or user.is_owner(self.uv)

    @cached_property
    def is_reported(self):
        """
        Return True if someone reported this UV
        """
        return self.reports.exists()

    def __str__(self):
        return "%s - %s" % (self.uv, self.author)

    def save(self, *args, **kwargs):
        if self.publish_date is None:
            self.publish_date = timezone.now()
        super(UVComment, self).save(*args, **kwargs)


class UVResult(models.Model):
    """
    Results got to an UV
    Views will be implemented after the first release
    Will list every UV done by an user
    Linked to user
              uv
    Contains a grade settings.SITH_PEDAGOGY_UV_RESULT_GRADE
             a semester (P/A)20xx
    """

    uv = models.ForeignKey(
        UV, related_name="results", verbose_name=_("uv"), on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="uv_results", verbose_name=("user"), on_delete=models.CASCADE
    )
    grade = models.CharField(
        _("grade"),
        max_length=10,
        choices=settings.SITH_PEDAGOGY_UV_RESULT_GRADE,
        default=settings.SITH_PEDAGOGY_UV_RESULT_GRADE[0][0],
    )
    semester = models.CharField(
        _("semester"),
        max_length=5,
        validators=[validators.RegexValidator("[AP][0-9]{3}")],
    )


class UVCommentReport(models.Model):
    """
    Report an inapropriate comment
    """

    comment = models.ForeignKey(
        UVComment,
        related_name="reports",
        verbose_name=_("report"),
        on_delete=models.CASCADE,
    )
    reporter = models.ForeignKey(
        User,
        related_name="reported_uv_comment",
        verbose_name=_("reporter"),
        on_delete=models.CASCADE,
    )
    reason = models.TextField(_("reason"))

    @cached_property
    def uv(self):
        return self.comment.uv

    def is_owned_by(self, user):
        """
        Can be created by a pedagogy admin, a superuser or a subscriber
        """
        return user.is_subscribed or user.is_owner(self.comment.uv)


# Custom serializers


class UVSerializer(serializers.ModelSerializer):
    """
    Custom seralizer for UVs
    Allow adding more informations like absolute_url
    """

    class Meta:
        model = UV
        fields = "__all__"

    absolute_url = serializers.SerializerMethodField()
    update_url = serializers.SerializerMethodField()
    delete_url = serializers.SerializerMethodField()

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_update_url(self, obj):
        return reverse("pedagogy:uv_update", kwargs={"uv_id": obj.id})

    def get_delete_url(self, obj):
        return reverse("pedagogy:uv_delete", kwargs={"uv_id": obj.id})
