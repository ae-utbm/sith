# Create your views here.
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

from core.models import User


class GeneratorView(TemplateView):
    template_name = "timetable/generator.jinja"


class UserTimetableView(UserPassesTestMixin, DetailView):
    model = User
    pk_url_kwarg = "user_id"
    template_name = "timetable/user_timetable.jinja"

    def test_func(self) -> bool | None:
        return self.request.user.id == self.kwargs[
            "user_id"
        ] or self.request.user.has_perm("timetable.view_timetable")
