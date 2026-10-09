from django.urls import path

from timetable.views import GeneratorView, UserTimetableView

urlpatterns = [
    path("", GeneratorView.as_view(), name="generator"),
    path("user/<int:user_id>", UserTimetableView.as_view(), name="user_timetable"),
]
