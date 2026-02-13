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

from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.views.widgets.markdown import MarkdownInput
from pedagogy.models import UE, UEComment, UECommentReport


class UEForm(forms.ModelForm):
    """Form handeling creation and edit of an UE."""

    class Meta:
        model = UE
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
        super().__init__(*args, **kwargs)
        self.fields["author"].queryset = User.objects.filter(id=author_id).all()
        self.fields["author"].initial = author_id


class StarList(forms.NumberInput):
    template_name = "pedagogy/starlist.jinja"

    def __init__(self, nubmer_of_stars=0):
        super().__init__(None)
        self.number_of_stars = nubmer_of_stars

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["number_of_stars"] = range(0, self.number_of_stars)
        context["translations"] = {"do_not_vote": _("Do not vote")}
        return context


class UECommentForm(forms.ModelForm):
    """Form handeling creation and edit of an UEComment."""

    class Meta:
        model = UEComment
        fields = (
            "author",
            "ue",
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
            "ue": forms.HiddenInput,
            "grade_global": StarList(5),
            "grade_utility": StarList(5),
            "grade_interest": StarList(5),
            "grade_teaching": StarList(5),
            "grade_work_load": StarList(5),
        }

    def __init__(self, author_id, ue_id, is_creation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["author"].queryset = User.objects.filter(id=author_id).all()
        self.fields["author"].initial = author_id
        self.fields["ue"].queryset = UE.objects.filter(id=ue_id).all()
        self.fields["ue"].initial = ue_id
        self.is_creation = is_creation

    def clean(self):
        self.cleaned_data = super().clean()
        ue = self.cleaned_data.get("ue")
        author = self.cleaned_data.get("author")

        if self.is_creation and ue and author and ue.has_user_already_commented(author):
            self.add_error(
                None,
                forms.ValidationError(
                    _("This user has already commented on this UE"), code="invalid"
                ),
            )

        return self.cleaned_data


class UECommentReportForm(forms.ModelForm):
    """Form handeling creation and edit of an UEReport."""

    class Meta:
        model = UECommentReport
        fields = ("comment", "reporter", "reason")
        widgets = {
            "comment": forms.HiddenInput,
            "reporter": forms.HiddenInput,
            "reason": MarkdownInput,
        }

    def __init__(self, reporter_id, comment_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reporter"].queryset = User.objects.filter(id=reporter_id).all()
        self.fields["reporter"].initial = reporter_id
        self.fields["comment"].queryset = UEComment.objects.filter(id=comment_id).all()
        self.fields["comment"].initial = comment_id


class UECommentModerationForm(forms.Form):
    """Form handeling bulk comment deletion."""

    accepted_reports = forms.ModelMultipleChoiceField(
        UECommentReport.objects.all(),
        label=_("Accepted reports"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    denied_reports = forms.ModelMultipleChoiceField(
        UECommentReport.objects.all(),
        label=_("Denied reports"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
