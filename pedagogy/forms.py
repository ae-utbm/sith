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
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import Widget
from django.templatetags.static import static

from core.views.forms import MarkdownInput
from core.models import User

from pedagogy.models import UV, UVComment, UVCommentReport


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
            "department",
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


class StarList(forms.NumberInput):
    template_name = "pedagogy/starlist.jinja"

    def __init__(self, nubmer_of_stars=0):
        super(StarList, self).__init__(None)
        self.number_of_stars = nubmer_of_stars

    def get_context(self, name, value, attrs):
        context = super(StarList, self).get_context(name, value, attrs)
        context["number_of_stars"] = range(0, self.number_of_stars)
        context["translations"] = {"do_not_vote": _("Do not vote")}
        return context


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
            "grade_global": StarList(5),
            "grade_utility": StarList(5),
            "grade_interest": StarList(5),
            "grade_teaching": StarList(5),
            "grade_work_load": StarList(5),
        }

    def __init__(self, author_id, uv_id, *args, **kwargs):
        super(UVCommentForm, self).__init__(*args, **kwargs)
        self.fields["author"].queryset = User.objects.filter(id=author_id).all()
        self.fields["author"].initial = author_id
        self.fields["uv"].queryset = UV.objects.filter(id=uv_id).all()
        self.fields["uv"].initial = uv_id


class UVCommentReportForm(forms.ModelForm):
    """
    Form handeling creation and edit of an UVReport
    """

    class Meta:
        model = UVCommentReport
        fields = ("comment", "reporter", "reason")
        widgets = {
            "comment": forms.HiddenInput,
            "reporter": forms.HiddenInput,
            "reason": MarkdownInput,
        }

    def __init__(self, reporter_id, comment_id, *args, **kwargs):
        super(UVCommentReportForm, self).__init__(*args, **kwargs)
        self.fields["reporter"].queryset = User.objects.filter(id=reporter_id).all()
        self.fields["reporter"].initial = reporter_id
        self.fields["comment"].queryset = UVComment.objects.filter(id=comment_id).all()
        self.fields["comment"].initial = comment_id


class UVCommentModerationForm(forms.Form):
    """
    Form handeling bulk comment deletion
    """

    accepted_reports = forms.ModelMultipleChoiceField(
        UVCommentReport.objects.all(),
        label=_("Accepted reports"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    denied_reports = forms.ModelMultipleChoiceField(
        UVCommentReport.objects.all(),
        label=_("Denied reports"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
