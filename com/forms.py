from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from club.models import Club
from com.models import News, NewsDate, Poster
from core.views.forms import SelectDateTime
from core.views.widgets.markdown import MarkdownInput


class PosterForm(forms.ModelForm):
    class Meta:
        model = Poster
        fields = [
            "name",
            "file",
            "club",
            "screens",
            "date_begin",
            "date_end",
            "display_time",
        ]
        widgets = {"screens": forms.CheckboxSelectMultiple}
        help_texts = {"file": _("Format: 16:9 | Resolution: 1920x1080")}

    date_begin = forms.DateTimeField(
        label=_("Start date"),
        widget=SelectDateTime,
        required=True,
        initial=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    date_end = forms.DateTimeField(
        label=_("End date"), widget=SelectDateTime, required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_com_admin:
            self.fields["club"].queryset = Club.objects.filter(
                id__in=self.user.clubs_with_rights
            )
            self.fields.pop("display_time")


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["type", "title", "club", "summary", "content", "author"]
        widgets = {
            "author": forms.HiddenInput,
            "summary": MarkdownInput,
            "content": MarkdownInput,
        }

    start_date = forms.DateTimeField(
        label=_("Start date"), widget=SelectDateTime, required=False
    )
    end_date = forms.DateTimeField(
        label=_("End date"), widget=SelectDateTime, required=False
    )
    until = forms.DateTimeField(label=_("Until"), widget=SelectDateTime, required=False)

    automoderation = forms.BooleanField(label=_("Automoderation"), required=False)

    def clean(self):
        self.cleaned_data = super().clean()
        if self.cleaned_data["type"] != "NOTICE":
            if not self.cleaned_data["start_date"]:
                self.add_error(
                    "start_date", ValidationError(_("This field is required."))
                )
            if not self.cleaned_data["end_date"]:
                self.add_error(
                    "end_date", ValidationError(_("This field is required."))
                )
            if (
                not self.has_error("start_date")
                and not self.has_error("end_date")
                and self.cleaned_data["start_date"] > self.cleaned_data["end_date"]
            ):
                self.add_error(
                    "end_date",
                    ValidationError(_("An event cannot end before its beginning.")),
                )
            if self.cleaned_data["type"] == "WEEKLY" and not self.cleaned_data["until"]:
                self.add_error("until", ValidationError(_("This field is required.")))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        ret = super().save()
        self.instance.dates.all().delete()
        if self.instance.type == "EVENT" or self.instance.type == "CALL":
            NewsDate(
                start_date=self.cleaned_data["start_date"],
                end_date=self.cleaned_data["end_date"],
                news=self.instance,
            ).save()
        elif self.instance.type == "WEEKLY":
            start_date = self.cleaned_data["start_date"]
            end_date = self.cleaned_data["end_date"]
            while start_date <= self.cleaned_data["until"]:
                NewsDate(
                    start_date=start_date, end_date=end_date, news=self.instance
                ).save()
                start_date += timedelta(days=7)
                end_date += timedelta(days=7)
        return ret
