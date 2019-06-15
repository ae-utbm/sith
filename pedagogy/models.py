# -*- coding:utf-8 -*
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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.conf import settings

from core.models import User

# Create your models here.


class UV(models.Model):
    """
    Contains infos about an UV (course)
    """

    def is_owned_by(self, user):
        """
        Can be created by superuser, root or pedagogy admin user
        """
        return user.is_in_group(settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)

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
        related_name="created_UVs",
        verbose_name=_("author"),
        null=False,
        blank=False,
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
    # Departments not implemented yet

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


class UVComment(models.Model):
    """
    A comment about an UV
    """

    pass


class UVCommentReport(models.Model):
    """
    Report an inapropriate comment
    """

    pass


class EducationDepartment(models.Model):
    """
    Education department of the school
    """

    pass


class StudyField(models.Model):
    """
    Speciality inside an Education Department
    """

    pass
