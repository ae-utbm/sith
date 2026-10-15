from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

from core.models import User
from core.views import TabedViewMixin


class TimetableTabsMixin(TabedViewMixin):
    tabs_title = _("Timetables")

    def get_list_of_tabs(self):
        res = [
            {
                "url": reverse("timetable:generator"),
                "slug": "generator",
                "name": _("Generator"),
            }
        ]
        if self.request.user.timetables.exists():
            res.append(
                {
                    "url": reverse(
                        "core:user_timetable", kwargs={"user_id": self.request.user.id}
                    ),
                    "slug": "saved",
                    "name": _("My timetables"),
                }
            )
        return res


class GeneratorView(TimetableTabsMixin, TemplateView):
    template_name = "timetable/generator.jinja"
    current_tab = "generator"


class UserTimetableView(UserPassesTestMixin, TimetableTabsMixin, DetailView):
    model = User
    pk_url_kwarg = "user_id"
    template_name = "timetable/user_timetable.jinja"
    current_tab = "saved"

    def test_func(self) -> bool | None:
        return self.request.user.id == self.kwargs[
            "user_id"
        ] or self.request.user.has_perm("timetable.view_timetable")

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "timetables": list(self.object.timetables.prefetch_related("slots"))
        }
