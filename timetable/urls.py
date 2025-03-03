from django.urls import path

from timetable.views import GeneratorView

urlpatterns = [path("generator/", GeneratorView.as_view(), name="generator")]
