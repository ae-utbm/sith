# Create your views here.

from django.views.generic import TemplateView


class GeneratorView(TemplateView):
    template_name = "timetable/generator.jinja"
