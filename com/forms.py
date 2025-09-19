from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.forms import CheckboxInput
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from club.models import Club
from club.widgets.ajax_select import AutoCompleteSelectClub
from com.models import News, NewsDate, Poster
from core.models import User
from core.utils import get_end_of_semester
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
        initial=timezone.now(),
    )
    date_end = forms.DateTimeField(
        label=_("End date"), widget=SelectDateTime, required=False
    )

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        if user.is_root or user.is_com_admin:
            self.fields["club"].widget = AutoCompleteSelectClub()
        else:
            self.fields["club"].queryset = Club.objects.having_board_member(user)


class NewsDateForm(forms.ModelForm):
    """Form to select the dates of an event."""

    required_css_class = "required"

    class Meta:
        model = NewsDate
        fields = ["start_date", "end_date"]
        widgets = {"start_date": SelectDateTime, "end_date": SelectDateTime}

    is_weekly = forms.BooleanField(
        label=_("Weekly event"),
        help_text=_("Weekly events will occur each week for a specified timespan."),
        widget=CheckboxInput(attrs={"class": "switch"}),
        initial=False,
        required=False,
    )
    occurrence_choices = [
        *[(str(i), _("%d times") % i) for i in range(2, 7)],
        ("SEMESTER_END", _("Until the end of the semester")),
    ]
    occurrences = forms.ChoiceField(
        label=_("Occurrences"),
        help_text=_("How much times should the event occur (including the first one)"),
        choices=occurrence_choices,
        initial="SEMESTER_END",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""

    @classmethod
    def get_occurrences(cls, number: int) -> tuple[str, str] | None:
        """Find the occurrence choice corresponding to numeric number of occurrences."""
        if number < 2:
            # If only 0 or 1 date, there cannot be weekly events
            return None
        # occurrences have all a numeric value, except "SEMESTER_END"
        str_num = str(number)
        occurrences = next((c for c in cls.occurrence_choices if c[0] == str_num), None)
        if occurrences:
            return occurrences
        return next((c for c in cls.occurrence_choices if c[0] == "SEMESTER_END"), None)

    def save(self, commit: bool = True, *, news: News):  # noqa FBT001
        # the base save method contains some checks we want to run
        # before doing our own logic
        super().save(commit=False)
        # delete existing dates before creating new ones
        news.dates.all().delete()
        if not self.cleaned_data.get("is_weekly"):
            self.instance.news = news
            return super().save(commit=commit)

        dates: list[NewsDate] = [self.instance]
        occurrences = self.cleaned_data.get("occurrences")
        start = self.instance.start_date
        end = self.instance.end_date
        if occurrences[0].isdigit():
            nb_occurrences = int(occurrences[0])
        else:  # to the end of the semester
            start_date = date(start.year, start.month, start.day)
            nb_occurrences = (get_end_of_semester(start_date) - start_date).days // 7
        dates.extend(
            [
                NewsDate(
                    start_date=start + relativedelta(weeks=i),
                    end_date=end + relativedelta(weeks=i),
                )
                for i in range(1, nb_occurrences)
            ]
        )
        for d in dates:
            d.news = news
        if not commit:
            return dates
        return NewsDate.objects.bulk_create(dates)


class NewsForm(forms.ModelForm):
    """Form to create or edit news."""

    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = News
        fields = ["title", "club", "summary", "content"]
        widgets = {
            "author": forms.HiddenInput,
            "summary": MarkdownInput,
            "content": MarkdownInput,
        }

    auto_publish = forms.BooleanField(
        label=_("Auto publication"),
        widget=CheckboxInput(attrs={"class": "switch"}),
        required=False,
    )

    def __init__(self, *args, author: User, date_form: NewsDateForm, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author
        self.date_form = date_form
        self.label_suffix = ""
        # if the author is an admin, he/she can choose any club,
        # otherwise, only clubs for which he/she is a board member can be selected
        if author.is_root or author.is_com_admin:
            self.fields["club"].widget = AutoCompleteSelectClub()
        else:
            self.fields["club"].queryset = Club.objects.having_board_member(author)

    def is_valid(self):
        return super().is_valid() and self.date_form.is_valid()

    def full_clean(self):
        super().full_clean()
        self.date_form.full_clean()

    def save(self, commit: bool = True):  # noqa FBT001
        self.instance.author = self.author
        if (self.author.is_com_admin or self.author.is_root) and (
            self.cleaned_data.get("auto_publish") is True
        ):
            self.instance.is_published = True
            self.instance.moderator = self.author
        else:
            self.instance.is_published = False
        created_news = super().save(commit=commit)
        self.date_form.save(commit=commit, news=created_news)
        return created_news
