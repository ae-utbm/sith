# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
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

from django import forms

from core.views.forms import MarkdownInput
from core.models import User

from pedagogy.models import UV, UVComment


class UVForm(forms.ModelForm):
    """
    Form handeling creation and edit of an UV
    """

    class Meta:
        model = UV
        fields = (
            "code",
            "author",
            "credit_type",
            "semester",
            "language",
            "credits",
            "hours_CM",
            "hours_TD",
            "hours_TP",
            "hours_THE",
            "hours_TE",
            "manager",
            "title",
            "objectives",
            "program",
            "skills",
            "key_concepts",
        )
        widgets = {
            "objectives": MarkdownInput,
            "program": MarkdownInput,
            "skills": MarkdownInput,
            "key_concepts": MarkdownInput,
            "author": forms.HiddenInput,
        }

    def __init__(self, author_id, *args, **kwargs):
        super(UVForm, self).__init__(*args, **kwargs)
        self.fields["author"].queryset = User.objects.filter(id=author_id).all()
        self.fields["author"].initial = author_id


class UVCommentForm(forms.ModelForm):
    """
    Form handeling creation and edit of an UVComment
    """

    class Meta:
        model = UVComment
        fields = (
            "author",
            "uv",
            "grade_global",
            "grade_utility",
            "grade_interest",
            "grade_teaching",
            "grade_work_load",
            "comment",
        )
        widgets = {
            "comment": MarkdownInput,
            "author": forms.HiddenInput,
            "uv": forms.HiddenInput,
        }

    def __init__(self, author_id, uv_id, *args, **kwargs):
        super(UVCommentForm, self).__init__(*args, **kwargs)
        self.fields["author"].queryset = User.objects.filter(id=author_id).all()
        self.fields["author"].initial = author_id
        self.fields["uv"].queryset = UV.objects.filter(id=uv_id).all()
        self.fields["uv"].initial = uv_id
