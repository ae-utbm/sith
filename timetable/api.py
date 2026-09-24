from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route

from core.utils import get_semester_code
from timetable.models import Timetable, TimetableSlot
from timetable.schemas import CreateTimetableSchema, TimetableSchema


@api_controller("/edt", urls_namespace="timetable")
class TimetableController(ControllerBase):
    @route.put("", auth=SessionAuth(), response={200: TimetableSchema}, url_name="save")
    def save_timetable(self, data: CreateTimetableSchema):
        user = self.context.request.user
        timetable, created = Timetable.objects.get_or_create(
            semester=get_semester_code(), user=user
        )
        if not created:
            timetable.slots.all().delete()
        if user.preferences.show_my_timetable != data.is_viewable:
            user.preferences.show_my_timetable = data.is_viewable
            user.preferences.save()
        slots = TimetableSlot.objects.bulk_create(
            [TimetableSlot(timetable=timetable, **s.model_dump()) for s in data.slots]
        )
        return TimetableSchema(
            id=timetable.id, semester=timetable.semester, slots=slots
        )
