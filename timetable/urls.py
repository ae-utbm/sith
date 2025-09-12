from django.urls import path

from timetable.views import GeneratorView

urlpatterns = [path("", GeneratorView.as_view(), name="generator")]
