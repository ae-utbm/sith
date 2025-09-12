# Create your views here.
from django.views.generic import TemplateView

from core.auth.mixins import FormerSubscriberMixin


class GeneratorView(FormerSubscriberMixin, TemplateView):
    template_name = "timetable/generator.jinja"
