# Create your views here.
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView


class GeneratorView(UserPassesTestMixin, TemplateView):
    template_name = "timetable/generator.jinja"

    def test_func(self):
        return self.request.user.is_subscribed
