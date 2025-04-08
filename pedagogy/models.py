#
# Copyright 2019
# - Sli <antoine@bartuccio.fr>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
from typing import Self

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models import Exists, OuterRef
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from core.models import User

# Create your models here.


class UE(models.Model):
    """Contains infos about an UE (course)."""

    code = models.CharField(
        _("code"),
        max_length=10,
        unique=True,
        validators=[
            validators.RegexValidator(
                regex="([A-Z0-9]+)",
                message=_(
                    "The code of an UE must only contains "
                    "uppercase characters without accent and numbers"
                ),
            )
        ],
    )
    author = models.ForeignKey(
        User,
        related_name="ue_created",
        verbose_name=_("author"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    credit_type = models.CharField(
        _("credit type"),
        max_length=10,
        choices=settings.SITH_PEDAGOGY_UE_TYPE,
        default=settings.SITH_PEDAGOGY_UE_TYPE[0][0],
    )
    manager = models.CharField(_("ue manager"), max_length=300)
    semester = models.CharField(
        _("semester"),
        max_length=20,
        choices=settings.SITH_PEDAGOGY_UE_SEMESTER,
        default=settings.SITH_PEDAGOGY_UE_SEMESTER[0][0],
    )
    language = models.CharField(
        _("language"),
        max_length=10,
        choices=settings.SITH_PEDAGOGY_UE_LANGUAGE,
        default=settings.SITH_PEDAGOGY_UE_LANGUAGE[0][0],
    )
    credits = models.PositiveIntegerField(_("credits"))

    department = models.CharField(
        _("departmenmt"),
        max_length=10,
        choices=settings.SITH_PROFILE_DEPARTMENTS,
        default=settings.SITH_PROFILE_DEPARTMENTS[-1][0],
    )

    # All texts about the UE
    title = models.CharField(_("title"), max_length=300)
    manager = models.CharField(_("ue manager"), max_length=300)
    objectives = models.TextField(_("objectives"))
    program = models.TextField(_("program"))
    skills = models.TextField(_("skills"))
    key_concepts = models.TextField(_("key concepts"))

    # Hours types CM, TD, TP, THE and TE
    # Kind of dirty but I have nothing else in mind for now
    hours_CM = models.PositiveIntegerField(_("hours CM"), default=0)
    hours_TD = models.PositiveIntegerField(_("hours TD"), default=0)
    hours_TP = models.PositiveIntegerField(_("hours TP"), default=0)
    hours_THE = models.PositiveIntegerField(_("hours THE"), default=0)
    hours_TE = models.PositiveIntegerField(_("hours TE"), default=0)

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse("pedagogy:ue_detail", kwargs={"ue_id": self.id})

    def __grade_average_generic(self, field):
        comments = self.comments.filter(**{field + "__gte": 0})
        if not comments.exists():
            return -1

        return int(sum(comments.values_list(field, flat=True)) / comments.count())

    def has_user_already_commented(self, user: User) -> bool:
        """Help prevent multiples comments from the same user.

        This function checks that no other comment has been posted by a specified user.

        Returns:
            True if the user has already posted a comment on this UE, else False.
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


class UECommentQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        if user.has_perms(["pedagogy.view_uecomment", "pedagogy.view_uecommentreport"]):
            # the user can view ue comment reports,
            # so he can view non-moderated comments
            return self
        if user.has_perm("pedagogy.view_uecomment"):
            return self.filter(reports=None)
        return self.filter(author=user)

    def annotate_is_reported(self) -> Self:
        return self.annotate(
            is_reported=Exists(UECommentReport.objects.filter(comment=OuterRef("pk")))
        )


class UEComment(models.Model):
    """A comment about an UE."""

    author = models.ForeignKey(
        User,
        related_name="ue_comments",
        verbose_name=_("author"),
        on_delete=models.CASCADE,
    )
    ue = models.ForeignKey(
        UE, related_name="comments", verbose_name=_("ue"), on_delete=models.CASCADE
    )
    comment = models.TextField(_("comment"), blank=True, default="")
    grade_global = models.IntegerField(
        _("global grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        default=-1,
    )
    grade_utility = models.IntegerField(
        _("utility grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        default=-1,
    )
    grade_interest = models.IntegerField(
        _("interest grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        default=-1,
    )
    grade_teaching = models.IntegerField(
        _("teaching grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        default=-1,
    )
    grade_work_load = models.IntegerField(
        _("work load grade"),
        validators=[validators.MinValueValidator(-1), validators.MaxValueValidator(4)],
        default=-1,
    )
    publish_date = models.DateTimeField(_("publish date"), blank=True)

    objects = UECommentQuerySet.as_manager()

    def __str__(self):
        return f"{self.ue} - {self.author}"

    def save(self, *args, **kwargs):
        if self.publish_date is None:
            self.publish_date = timezone.now()
        super().save(*args, **kwargs)


# TODO : it seems that some views were meant to be implemented
#        to use this model.
#        However, it seems that the implementation finally didn't happen.
#        It should be discussed, when possible, of what to do with that :
#        - go on and finally implement the UE results features ?
#        - or fuck go back and remove this model ?
class UEResult(models.Model):
    """Results got to an UE.

    Views will be implemented after the first release
    Will list every UE done by an user
    Linked to user and ue
    Contains a grade settings.SITH_PEDAGOGY_UE_RESULT_GRADE
             a semester (P/A)20xx.
    """

    ue = models.ForeignKey(
        UE, related_name="results", verbose_name=_("ue"), on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name="ue_results",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    grade = models.CharField(
        _("grade"),
        max_length=10,
        choices=settings.SITH_PEDAGOGY_UE_RESULT_GRADE,
        default=settings.SITH_PEDAGOGY_UE_RESULT_GRADE[0][0],
    )
    semester = models.CharField(
        _("semester"),
        max_length=5,
        validators=[validators.RegexValidator("[AP][0-9]{3}")],
    )

    def __str__(self):
        return f"{self.user.username} ; {self.ue.code} ; {self.grade}"


class UECommentReport(models.Model):
    """Report an inapropriate comment."""

    comment = models.ForeignKey(
        UEComment,
        related_name="reports",
        verbose_name=_("report"),
        on_delete=models.CASCADE,
    )
    reporter = models.ForeignKey(
        User,
        related_name="reported_ue_comment",
        verbose_name=_("reporter"),
        on_delete=models.CASCADE,
    )
    reason = models.TextField(_("reason"))

    def __str__(self):
        return f"{self.reporter.username} : {self.reason}"

    @cached_property
    def ue(self):
        return self.comment.ue
