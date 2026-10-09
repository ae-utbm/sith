from django.test import TestCase
from django.urls import reverse

from core.baker_recipes import subscriber_user
from timetable.models import TimetableSlot


class TestSaveTimetable(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = subscriber_user.make()
        cls.payload = {
            "is_viewable": True,
            "slots": [
                {"weekday": TimetableSlot.WeekDay.MONDAY, "start_at": 32, "end_at": 40},
                {"weekday": TimetableSlot.WeekDay.MONDAY, "start_at": 41, "end_at": 49},
                {"weekday": TimetableSlot.WeekDay.FRIDAY, "start_at": 52, "end_at": 64},
            ],
        }
        cls.url = reverse("api:timetable:save", kwargs={"user_id": cls.user.id})
